"""
Chat history management service for persistent Ghost AI conversations
"""

import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.models.database import ChatMessageDB, UserSessionDB
from app.models.schemas import ChatMessage
from app.services.session_manager import get_session_manager


class ChatManager:
    """Manages chat history and messages for Ghost AI conversations"""
    
    def __init__(self):
        self.session_manager = get_session_manager()
        self.max_messages_per_session = 1000  # Limit to prevent excessive storage
        self.message_retention_days = 30  # Keep messages for 30 days
    
    async def add_message(
        self, 
        session_id: str, 
        content: str, 
        sender: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatMessage]:
        """Add a new chat message to a session"""
        # Validate session exists
        if not await self.session_manager.validate_session(session_id):
            return None
        
        async with AsyncSessionLocal() as db:
            # Create new message
            message_id = str(uuid.uuid4())
            db_message = ChatMessageDB(
                id=message_id,
                content=content,
                sender=sender,
                context=context or {},
                session_id=session_id
            )
            
            db.add(db_message)
            await db.commit()
            await db.refresh(db_message)
            
            # Update session activity
            await self.session_manager.get_session(session_id, update_activity=True)
            
            # Clean up old messages if we exceed the limit
            await self._cleanup_old_messages(session_id, db)
            
            return ChatMessage(
                id=db_message.id,
                content=db_message.content,
                sender=db_message.sender,
                timestamp=db_message.timestamp,
                context=db_message.context
            )
    
    async def get_session_messages(
        self, 
        session_id: str, 
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[ChatMessage]:
        """Get chat messages for a session"""
        async with AsyncSessionLocal() as db:
            query = (
                select(ChatMessageDB)
                .where(ChatMessageDB.session_id == session_id)
                .order_by(ChatMessageDB.timestamp.desc())
            )
            
            if limit:
                query = query.limit(limit)
            
            if offset > 0:
                query = query.offset(offset)
            
            result = await db.execute(query)
            messages = result.scalars().all()
            
            # Return in chronological order (oldest first)
            return [
                ChatMessage(
                    id=msg.id,
                    content=msg.content,
                    sender=msg.sender,
                    timestamp=msg.timestamp,
                    context=msg.context
                )
                for msg in reversed(messages)
            ]
    
    async def get_recent_messages(self, session_id: str, count: int = 10) -> List[ChatMessage]:
        """Get the most recent messages for context"""
        return await self.get_session_messages(session_id, limit=count)
    
    async def get_message(self, session_id: str, message_id: str) -> Optional[ChatMessage]:
        """Get a specific message"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ChatMessageDB).where(
                    ChatMessageDB.id == message_id,
                    ChatMessageDB.session_id == session_id
                )
            )
            
            db_message = result.scalar_one_or_none()
            if not db_message:
                return None
            
            return ChatMessage(
                id=db_message.id,
                content=db_message.content,
                sender=db_message.sender,
                timestamp=db_message.timestamp,
                context=db_message.context
            )
    
    async def delete_message(self, session_id: str, message_id: str) -> bool:
        """Delete a specific message"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(ChatMessageDB).where(
                    ChatMessageDB.id == message_id,
                    ChatMessageDB.session_id == session_id
                )
            )
            
            db_message = result.scalar_one_or_none()
            if not db_message:
                return False
            
            await db.delete(db_message)
            await db.commit()
            
            # Update session activity
            await self.session_manager.get_session(session_id, update_activity=True)
            
            return True
    
    async def clear_session_history(self, session_id: str) -> bool:
        """Clear all chat history for a session"""
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(ChatMessageDB).where(ChatMessageDB.session_id == session_id)
            )
            await db.commit()
            
            # Update session activity
            await self.session_manager.get_session(session_id, update_activity=True)
            
            return True
    
    async def get_message_count(self, session_id: str) -> int:
        """Get the number of messages in a session"""
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(func.count(ChatMessageDB.id))
                .where(ChatMessageDB.session_id == session_id)
            )
            return result.scalar() or 0
    
    async def search_messages(
        self, 
        session_id: str, 
        query: str, 
        sender: Optional[str] = None
    ) -> List[ChatMessage]:
        """Search messages by content"""
        async with AsyncSessionLocal() as db:
            search_query = (
                select(ChatMessageDB)
                .where(
                    ChatMessageDB.session_id == session_id,
                    ChatMessageDB.content.ilike(f"%{query}%")
                )
            )
            
            if sender:
                search_query = search_query.where(ChatMessageDB.sender == sender)
            
            search_query = search_query.order_by(ChatMessageDB.timestamp.desc())
            
            result = await db.execute(search_query)
            messages = result.scalars().all()
            
            return [
                ChatMessage(
                    id=msg.id,
                    content=msg.content,
                    sender=msg.sender,
                    timestamp=msg.timestamp,
                    context=msg.context
                )
                for msg in messages
            ]
    
    async def get_conversation_context(self, session_id: str, max_messages: int = 20) -> str:
        """Get conversation context as a formatted string for AI"""
        messages = await self.get_recent_messages(session_id, max_messages)
        
        if not messages:
            return "No previous conversation history."
        
        context_lines = []
        for msg in messages:
            timestamp = msg.timestamp.strftime("%H:%M")
            context_lines.append(f"[{timestamp}] {msg.sender}: {msg.content}")
        
        return "\n".join(context_lines)
    
    async def add_ghost_response(
        self, 
        session_id: str, 
        response: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatMessage]:
        """Add a Ghost AI response message"""
        return await self.add_message(session_id, response, "ghost", context)
    
    async def add_user_message(
        self, 
        session_id: str, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[ChatMessage]:
        """Add a user message"""
        return await self.add_message(session_id, message, "user", context)
    
    async def _cleanup_old_messages(self, session_id: str, db: AsyncSession):
        """Clean up old messages if we exceed the limit"""
        # Count current messages
        result = await db.execute(
            select(func.count(ChatMessageDB.id))
            .where(ChatMessageDB.session_id == session_id)
        )
        message_count = result.scalar() or 0
        
        if message_count > self.max_messages_per_session:
            # Delete oldest messages
            messages_to_delete = message_count - self.max_messages_per_session
            
            # Get oldest message IDs
            result = await db.execute(
                select(ChatMessageDB.id)
                .where(ChatMessageDB.session_id == session_id)
                .order_by(ChatMessageDB.timestamp.asc())
                .limit(messages_to_delete)
            )
            old_message_ids = result.scalars().all()
            
            # Delete old messages
            if old_message_ids:
                await db.execute(
                    delete(ChatMessageDB)
                    .where(ChatMessageDB.id.in_(old_message_ids))
                )
    
    async def cleanup_old_messages_globally(self):
        """Clean up old messages across all sessions"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.message_retention_days)
        
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(ChatMessageDB)
                .where(ChatMessageDB.timestamp < cutoff_date)
            )
            await db.commit()
    
    async def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """Get statistics about a session's chat history"""
        async with AsyncSessionLocal() as db:
            # Total message count
            total_result = await db.execute(
                select(func.count(ChatMessageDB.id))
                .where(ChatMessageDB.session_id == session_id)
            )
            total_messages = total_result.scalar() or 0
            
            # User message count
            user_result = await db.execute(
                select(func.count(ChatMessageDB.id))
                .where(
                    ChatMessageDB.session_id == session_id,
                    ChatMessageDB.sender == "user"
                )
            )
            user_messages = user_result.scalar() or 0
            
            # Ghost message count
            ghost_result = await db.execute(
                select(func.count(ChatMessageDB.id))
                .where(
                    ChatMessageDB.session_id == session_id,
                    ChatMessageDB.sender == "ghost"
                )
            )
            ghost_messages = ghost_result.scalar() or 0
            
            # First and last message timestamps
            first_result = await db.execute(
                select(ChatMessageDB.timestamp)
                .where(ChatMessageDB.session_id == session_id)
                .order_by(ChatMessageDB.timestamp.asc())
                .limit(1)
            )
            first_message_time = first_result.scalar()
            
            last_result = await db.execute(
                select(ChatMessageDB.timestamp)
                .where(ChatMessageDB.session_id == session_id)
                .order_by(ChatMessageDB.timestamp.desc())
                .limit(1)
            )
            last_message_time = last_result.scalar()
            
            return {
                "total_messages": total_messages,
                "user_messages": user_messages,
                "ghost_messages": ghost_messages,
                "first_message_at": first_message_time,
                "last_message_at": last_message_time,
                "conversation_duration": (
                    last_message_time - first_message_time
                    if first_message_time and last_message_time
                    else None
                )
            }


# Global chat manager instance
_chat_manager: Optional[ChatManager] = None


def get_chat_manager() -> ChatManager:
    """Get the global chat manager instance"""
    global _chat_manager
    if _chat_manager is None:
        _chat_manager = ChatManager()
    return _chat_manager