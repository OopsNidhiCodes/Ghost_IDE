"""
Session management service with Redis for active sessions and PostgreSQL for persistence
"""

import json
import uuid
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
    CodeFile, CodeFileCreate, CodeFileUpdate,
    ChatMessage, UserPreferences
)


class SessionManager:
    """Manages user sessions with in-memory storage for local development"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self._redis = None  # Disabled for local development
        self._memory_sessions: Dict[str, Dict] = {}  # In-memory session storage
        self.session_ttl = 3600 * 24  # 24 hours for active sessions
        self.cleanup_interval = 3600  # 1 hour cleanup interval
        
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
        
        # Create session in PostgreSQL
        async with AsyncSessionLocal() as db:
            db_session = UserSessionDB(
                id=session_id,
                current_language=session_data.current_language.value,
                preferences=session_data.preferences.model_dump()
            )
            
            db.add(db_session)
            await db.commit()
            await db.refresh(db_session)
        
        # Create session object
        session = UserSession(
            id=session_id,
            current_language=session_data.current_language,
            preferences=session_data.preferences,
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
            session.preferences = session_update.preferences
        
        session.last_activity = datetime.utcnow()
        
        # Update in PostgreSQL
        async with AsyncSessionLocal() as db:
            update_data = {"last_activity": session.last_activity}
            if session_update.current_language is not None:
                update_data["current_language"] = session_update.current_language.value
            if session_update.preferences is not None:
                update_data["preferences"] = session_update.preferences.model_dump()
            
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
            file_data['last_modified'] = file_data['last_modified']
        
        for msg in session_data['chat_history']:
            msg['timestamp'] = msg['timestamp']
        
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
        ttl = await redis.ttl(session_key)
        
        return {
            "session_id": session_id,
            "created_at": session.created_at,
            "last_activity": session.last_activity,
            "is_active": ttl > 0,
            "expires_in_seconds": ttl if ttl > 0 else None,
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


async def cleanup_sessions_task():
    """Background task for cleaning up expired sessions"""
    session_manager = get_session_manager()
    await session_manager.cleanup_expired_sessions()