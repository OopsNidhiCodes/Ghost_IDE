"""
Message routing service for WebSocket communication
Provides high-level interface for other services to send WebSocket messages
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.services.websocket_manager import connection_manager
from app.models.websocket_schemas import (
    WebSocketMessage,
    WebSocketMessageType,
    ExecutionStartMessage,
    ExecutionOutputMessage,
    ExecutionCompleteMessage,
    AIResponseMessage,
    AITypingMessage,
    HookTriggeredMessage,
    SessionUpdateMessage
)
from app.models.schemas import ExecutionResult, ChatMessage

logger = logging.getLogger(__name__)


class MessageRouter:
    """Routes messages to appropriate WebSocket connections"""
    
    def __init__(self):
        self.manager = connection_manager
    
    async def notify_execution_start(
        self, 
        session_id: str, 
        language: str, 
        code_preview: str,
        execution_id: Optional[str] = None
    ):
        """
        Notify clients that code execution has started
        
        Args:
            session_id: Target session ID
            language: Programming language
            code_preview: First 100 characters of code
            execution_id: Optional execution identifier
        """
        try:
            message = ExecutionStartMessage(
                session_id=session_id,
                data={
                    "language": language,
                    "code_preview": code_preview[:100],
                    "execution_id": execution_id or f"exec_{datetime.utcnow().timestamp()}"
                }
            )
            await self.manager.send_to_session(session_id, message)
            logger.debug(f"Sent execution start notification to session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to send execution start notification: {e}")
    
    async def stream_execution_output(
        self, 
        session_id: str, 
        output: str, 
        stream: str = "stdout",
        execution_id: Optional[str] = None
    ):
        """
        Stream code execution output to clients
        
        Args:
            session_id: Target session ID
            output: Output text
            stream: Output stream type (stdout/stderr)
            execution_id: Optional execution identifier
        """
        try:
            message = ExecutionOutputMessage(
                session_id=session_id,
                data={
                    "output": output,
                    "stream": stream,
                    "execution_id": execution_id
                }
            )
            await self.manager.send_to_session(session_id, message)
            logger.debug(f"Streamed {len(output)} chars to session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to stream execution output: {e}")
    
    async def notify_execution_complete(
        self, 
        session_id: str, 
        result: ExecutionResult,
        execution_id: Optional[str] = None
    ):
        """
        Notify clients that code execution has completed
        
        Args:
            session_id: Target session ID
            result: Execution result
            execution_id: Optional execution identifier
        """
        try:
            message = ExecutionCompleteMessage(
                session_id=session_id,
                data={
                    "result": result.model_dump(),
                    "execution_id": execution_id
                }
            )
            await self.manager.send_to_session(session_id, message)
            logger.debug(f"Sent execution complete notification to session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to send execution complete notification: {e}")
    
    async def send_ai_response(
        self, 
        session_id: str, 
        message: ChatMessage,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Send Ghost AI response to clients
        
        Args:
            session_id: Target session ID
            message: Chat message from AI
            context: Optional context information
        """
        try:
            ws_message = AIResponseMessage(
                session_id=session_id,
                data={
                    "message": message.model_dump(),
                    "context": context or {}
                }
            )
            await self.manager.send_to_session(session_id, ws_message)
            logger.debug(f"Sent AI response to session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to send AI response: {e}")
    
    async def set_ai_typing(self, session_id: str, is_typing: bool = True):
        """
        Set Ghost AI typing indicator
        
        Args:
            session_id: Target session ID
            is_typing: Whether AI is typing
        """
        try:
            message = AITypingMessage(
                session_id=session_id,
                data={"is_typing": is_typing}
            )
            await self.manager.send_to_session(session_id, message)
            logger.debug(f"Set AI typing={is_typing} for session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to set AI typing indicator: {e}")
    
    async def notify_hook_triggered(
        self, 
        session_id: str, 
        hook_type: str, 
        context: Dict[str, Any]
    ):
        """
        Notify clients that a hook has been triggered
        
        Args:
            session_id: Target session ID
            hook_type: Type of hook (on_run, on_error, on_save)
            context: Hook context data
        """
        try:
            message = HookTriggeredMessage(
                session_id=session_id,
                data={
                    "hook_type": hook_type,
                    "context": context
                }
            )
            await self.manager.send_to_session(session_id, message)
            logger.debug(f"Sent hook notification ({hook_type}) to session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to send hook notification: {e}")
    
    async def notify_session_update(
        self, 
        session_id: str, 
        update_type: str, 
        details: Dict[str, Any]
    ):
        """
        Notify clients of session updates
        
        Args:
            session_id: Target session ID
            update_type: Type of update (file_added, file_updated, preferences_changed)
            details: Update details
        """
        try:
            message = SessionUpdateMessage(
                session_id=session_id,
                data={
                    "update_type": update_type,
                    "details": details
                }
            )
            await self.manager.send_to_session(session_id, message)
            logger.debug(f"Sent session update ({update_type}) to session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to send session update: {e}")
    
    async def notify_file_saved(
        self, 
        session_id: str, 
        file_id: str, 
        file_name: str,
        language: str
    ):
        """
        Notify clients that a file has been saved
        
        Args:
            session_id: Target session ID
            file_id: File identifier
            file_name: File name
            language: Programming language
        """
        try:
            message = WebSocketMessage(
                type=WebSocketMessageType.FILE_SAVED,
                session_id=session_id,
                data={
                    "file_id": file_id,
                    "file_name": file_name,
                    "language": language,
                    "saved_at": datetime.utcnow().isoformat()
                }
            )
            await self.manager.send_to_session(session_id, message)
            logger.debug(f"Sent file saved notification to session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to send file saved notification: {e}")
    
    async def send_error_to_session(
        self, 
        session_id: str, 
        error: str, 
        detail: str = "", 
        code: int = 500
    ):
        """
        Send error message to all connections in a session
        
        Args:
            session_id: Target session ID
            error: Error message
            detail: Additional error details
            code: Error code
        """
        await self.manager.send_session_error(session_id, error, detail, code)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get WebSocket connection statistics
        
        Returns:
            dict: Connection statistics
        """
        return {
            "total_connections": self.manager.get_total_connections(),
            "active_sessions": self.manager.get_active_sessions(),
            "session_count": len(self.manager.get_active_sessions())
        }


# Global message router instance
message_router = MessageRouter()