"""
Session management service with Redis for active sessions and PostgreSQL for persistence
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
# from redis.asyncio import Redis  # Disabled for local development
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.database import UserSessionDB, CodeFileDB, ChatMessageDB
from app.models.schemas import (
    UserSession, UserSessionCreate, UserSessionUpdate,
    CodeFile,
    ChatMessage, UserPreferences,
    SessionSyncRequest
)

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages user sessions with in-memory storage for local development"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis = None  # Disabled for local development
        self._memory_sessions: Dict[str, Dict] = {}  # In-memory session storage
        self.session_ttl = 3600 * 24  # 24 hours for active sessions
        self.cleanup_interval = 3600  # 1 hour cleanup interval
    
    @staticmethod
    def _sanitize_text(value: Optional[str]) -> Optional[str]:
        """Remove angle brackets to mitigate simple script injections"""
        if value is None:
            return None
        return value.replace("<", "").replace(">", "")
    
    @staticmethod
    def _coerce_datetime(value: Optional[Any], fallback: Optional[datetime] = None) -> datetime:
        """Convert string or datetime into datetime object"""
        if value is None:
            return fallback or datetime.utcnow()
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return fallback or datetime.utcnow()
    
    def _sanitize_preferences(self, preferences: UserPreferences) -> UserPreferences:
        """Ensure preference strings are safe"""
        pref_data = preferences.model_dump()
        pref_data["theme"] = self._sanitize_text(pref_data.get("theme", "ghost-dark")) or "ghost-dark"
        return UserPreferences(**pref_data)
        
    async def get_redis(self):
        """Get Redis connection - disabled for local development"""
        return None
    
    async def close(self):
        """Close Redis connection - disabled for local development"""
        self._memory_sessions.clear()
    
    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"session:{session_id}"
    
    def _active_sessions_key(self) -> str:
        """Generate Redis key for active sessions set"""
        return "active_sessions"
    
    async def create_session(self, session_data: UserSessionCreate) -> UserSession:
        """Create a new session in both Redis and PostgreSQL"""
        session_id = str(uuid.uuid4())
        
        preferences = self._sanitize_preferences(session_data.preferences)
        
        # Create session in PostgreSQL
        async with AsyncSessionLocal() as db:
            db_session = UserSessionDB(
                id=session_id,
                current_language=session_data.current_language.value,
                preferences=preferences.model_dump()
            )
            
            db.add(db_session)
            await db.commit()
            await db.refresh(db_session)
        
        # Create session object
        session = UserSession(
            id=session_id,
            current_language=session_data.current_language,
            preferences=preferences,
            files=[],
            chat_history=[],
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        # Store in memory for active session management
        await self._store_active_session(session)
        
        return session
    
    async def get_session(self, session_id: str, update_activity: bool = True) -> Optional[UserSession]:
        """Get session from memory first, fallback to PostgreSQL"""
        
        # Try to get from memory first (active sessions)
        session_key = self._session_key(session_id)
        session_data = self._memory_sessions.get(session_key)
        
        if session_data:
            # Parse from memory
            session = UserSession(**session_data)
            
            if update_activity:
                # Update activity timestamp
                session.last_activity = datetime.utcnow()
                await self._store_active_session(session)
            
            return session
        
        # Fallback to PostgreSQL
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserSessionDB)
                .options(
                    selectinload(UserSessionDB.files),
                    selectinload(UserSessionDB.chat_messages)
                )
                .where(UserSessionDB.id == session_id)
            )
            
            db_session = result.scalar_one_or_none()
            
            if not db_session:
                return None
            
            # Update last activity if requested
            if update_activity:
                await db.execute(
                    update(UserSessionDB)
                    .where(UserSessionDB.id == session_id)
                    .values(last_activity=datetime.utcnow())
                )
                await db.commit()
            
            # Convert to session object
            files = [
                CodeFile(
                    id=f.id,
                    name=f.name,
                    content=f.content,
                    language=f.language,
                    last_modified=f.last_modified
                )
                for f in db_session.files
            ]
            
            chat_history = [
                ChatMessage(
                    id=msg.id,
                    content=msg.content,
                    sender=msg.sender,
                    timestamp=msg.timestamp,
                    context=msg.context
                )
                for msg in db_session.chat_messages
            ]
            
            session = UserSession(
                id=db_session.id,
                current_language=db_session.current_language,
                preferences=UserPreferences(**db_session.preferences),
                files=files,
                chat_history=chat_history,
                created_at=db_session.created_at,
                last_activity=db_session.last_activity if not update_activity else datetime.utcnow()
            )
            
            # Store in memory for future quick access
            await self._store_active_session(session)
            
            return session
    
    async def update_session(self, session_id: str, session_update: UserSessionUpdate) -> Optional[UserSession]:
        """Update session in both Redis and PostgreSQL"""
        # Get current session
        session = await self.get_session(session_id, update_activity=False)
        if not session:
            return None
        
        # Apply updates
        if session_update.current_language is not None:
            session.current_language = session_update.current_language
        if session_update.preferences is not None:
            session.preferences = self._sanitize_preferences(session_update.preferences)
        
        session.last_activity = datetime.utcnow()
        
        # Update in PostgreSQL
        async with AsyncSessionLocal() as db:
            update_data = {"last_activity": session.last_activity}
            if session_update.current_language is not None:
                update_data["current_language"] = session_update.current_language.value
            if session_update.preferences is not None:
                update_data["preferences"] = session.preferences.model_dump()
            
            await db.execute(
                update(UserSessionDB)
                .where(UserSessionDB.id == session_id)
                .values(**update_data)
            )
            await db.commit()
        
        # Update in memory
        await self._store_active_session(session)
        
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from both memory and PostgreSQL"""
        
        # Remove from memory
        session_key = self._session_key(session_id)
        self._memory_sessions.pop(session_key, None)
        
        # Remove from PostgreSQL
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(UserSessionDB).where(UserSessionDB.id == session_id)
            )
            db_session = result.scalar_one_or_none()
            
            if db_session:
                await db.delete(db_session)
                await db.commit()
                return True
        
        return False
    
    async def _store_active_session(self, session: UserSession):
        """Store session in memory for active session management"""
        
        session_key = self._session_key(session.id)
        session_data = session.model_dump(mode='json')
        
        # Convert datetime objects to ISO strings for JSON serialization
        session_data['created_at'] = session.created_at.isoformat()
        session_data['last_activity'] = session.last_activity.isoformat()
        
        for file_data in session_data['files']:
            last_modified = file_data.get('last_modified')
            if isinstance(last_modified, datetime):
                file_data['last_modified'] = last_modified.isoformat()
        
        for msg in session_data['chat_history']:
            timestamp = msg.get('timestamp')
            if isinstance(timestamp, datetime):
                msg['timestamp'] = timestamp.isoformat()
        
        # Store session data in memory
        self._memory_sessions[session_key] = session_data
    
    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return [key.replace("session:", "") for key in self._memory_sessions.keys()]
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions from memory and inactive sessions from PostgreSQL"""
        
        # Clean up old sessions from PostgreSQL (older than 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        try:
            async with AsyncSessionLocal() as db:
                # Delete old sessions
                await db.execute(
                    delete(UserSessionDB)
                    .where(UserSessionDB.last_activity < cutoff_date)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
            # Don't fail if database cleanup fails
    
    async def sync_session(self, session_id: str, sync_data: SessionSyncRequest) -> Optional[UserSession]:
        """Synchronize in-memory session data with payload from clients"""
        session = await self.get_session(session_id, update_activity=False)
        if not session:
            return None
        
        # Update preferences
        if sync_data.preferences:
            session.preferences = self._sanitize_preferences(sync_data.preferences)
        
        # Update last activity
        session.last_activity = self._coerce_datetime(sync_data.last_activity, session.last_activity)
        
        # Update cached files (in-memory only for now)
        if sync_data.files:
            normalized_files = []
            for file_payload in sync_data.files:
                normalized_files.append(
                    CodeFile(
                        id=file_payload.id or str(uuid.uuid4()),
                        name=file_payload.name,
                        content=file_payload.content,
                        language=file_payload.language or session.current_language.value,
                        last_modified=self._coerce_datetime(
                            file_payload.last_modified,
                            datetime.utcnow()
                        )
                    )
                )
            session.files = normalized_files
        
        # Update chat history snapshot
        if sync_data.chat_history:
            normalized_messages = []
            for msg in sync_data.chat_history:
                normalized_messages.append(
                    ChatMessage(
                        id=msg.id or str(uuid.uuid4()),
                        content=msg.content,
                        sender=msg.sender,
                        timestamp=self._coerce_datetime(msg.timestamp, datetime.utcnow()),
                        context=msg.context
                    )
                )
            session.chat_history = normalized_messages
        
        # Persist preference / activity updates
        async with AsyncSessionLocal() as db:
            update_data = {"last_activity": session.last_activity}
            if sync_data.preferences:
                update_data["preferences"] = session.preferences.model_dump()
            
            await db.execute(
                update(UserSessionDB)
                .where(UserSessionDB.id == session_id)
                .values(**update_data)
            )
            await db.commit()
        
        await self._store_active_session(session)
        return session
    
    async def restore_session(self, session_id: str) -> Optional[UserSession]:
        """Restore a session from PostgreSQL to Redis (for returning users)"""
        # This is essentially the same as get_session, but explicitly for restoration
        return await self.get_session(session_id, update_activity=True)
    
    async def validate_session(self, session_id: str) -> bool:
        """Validate that a session exists and is accessible"""
        try:
            session = await self.get_session(session_id, update_activity=False)
            return session is not None
        except Exception:
            return False
    
    async def get_session_security_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get security information about a session"""
        session = await self.get_session(session_id, update_activity=False)
        if not session:
            return None
        
        redis = await self.get_redis()
        session_key = self._session_key(session_id)
        ttl = None
        if redis:
            ttl = await redis.ttl(session_key)
        elif session_key in self._memory_sessions:
            ttl = self.session_ttl
        
        return {
            "session_id": session_id,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "is_active": ttl is not None,
            "expires_in_seconds": ttl,
            "file_count": len(session.files),
            "message_count": len(session.chat_history)
        }


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance"""
    global _session_manager
    if _session_manager is None:
        import os
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _session_manager = SessionManager(redis_url)
    return _session_manager


session_manager = get_session_manager()


async def cleanup_sessions_task():
    """Background task for cleaning up expired sessions"""
    session_manager = get_session_manager()
    await session_manager.cleanup_expired_sessions()