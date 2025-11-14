"""
Hook Manager Service - Manages automated AI responses to code events
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from pydantic import BaseModel, Field

from .ghost_ai import GhostAIService, HookEvent, HookEventType, AIContext
from .websocket_manager import connection_manager
from ..models.websocket_schemas import WebSocketMessage, WebSocketMessageType
from ..models.schemas import LanguageType, ChatMessage

logger = logging.getLogger(__name__)


class HookStatus(str, Enum):
    """Status of hook execution"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HookExecution(BaseModel):
    """Model for tracking hook execution"""
    id: str
    event: HookEvent
    status: HookStatus = HookStatus.PENDING
    ai_response: Optional[str] = None
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None


class HookManagerService:
    """
    Service for managing automated AI responses to code execution events
    """
    
    def __init__(self, ghost_ai_service: GhostAIService):
        """Initialize the hook manager"""
        self.ghost_ai = ghost_ai_service
        self.hook_executions: Dict[str, HookExecution] = {}
        self.event_listeners: Dict[HookEventType, List[Callable]] = {
            HookEventType.ON_RUN: [],
            HookEventType.ON_ERROR: [],
            HookEventType.ON_SAVE: []
        }
        self.enabled_hooks: Dict[HookEventType, bool] = {
            HookEventType.ON_RUN: True,
            HookEventType.ON_ERROR: True,
            HookEventType.ON_SAVE: True
        }
        
        # Statistics
        self.hook_stats = {
            "total_events": 0,
            "successful_responses": 0,
            "failed_responses": 0,
            "events_by_type": {hook_type.value: 0 for hook_type in HookEventType}
        }
        
        logger.info("Hook Manager Service initialized")
    
    async def trigger_hook(
        self, 
        event_type: HookEventType, 
        session_id: str, 
        data: Dict[str, Any],
        context: Optional[AIContext] = None
    ) -> Optional[str]:
        """
        Trigger a hook event and generate AI response
        
        Args:
            event_type: Type of hook event
            session_id: Session ID where the event occurred
            data: Event data (code, error, etc.)
            context: AI context for generating response
            
        Returns:
            Optional[str]: AI response if successful, None if failed
        """
        if not self.enabled_hooks.get(event_type, False):
            logger.debug(f"Hook {event_type} is disabled, skipping")
            return None
        
        # Create hook event
        event = HookEvent(
            event_type=event_type,
            session_id=session_id,
            data=data
        )
        
        # Create execution tracking
        execution_id = f"{session_id}_{event_type.value}_{datetime.utcnow().timestamp()}"
        execution = HookExecution(
            id=execution_id,
            event=event
        )
        
        self.hook_executions[execution_id] = execution
        self.hook_stats["total_events"] += 1
        self.hook_stats["events_by_type"][event_type.value] += 1
        
        logger.info(f"Triggering hook {event_type} for session {session_id}")
        
        try:
            # Update status to processing
            execution.status = HookStatus.PROCESSING
            
            # Generate AI context if not provided
            if context is None:
                context = AIContext(
                    session_id=session_id,
                    current_code=data.get("code", ""),
                    language=LanguageType(data.get("language", "python")),
                    recent_errors=[data.get("error")] if data.get("error") else []
                )
            
            # Generate AI response
            ai_response = await self.ghost_ai.react_to_event(event, context)
            
            # Update execution
            execution.ai_response = ai_response
            execution.status = HookStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
            
            self.hook_stats["successful_responses"] += 1
            
            # Send AI response via WebSocket
            await self._send_ai_response(session_id, ai_response, event_type)
            
            # Call registered listeners
            await self._call_event_listeners(event_type, event, ai_response)
            
            logger.info(f"Hook {event_type} completed successfully for session {session_id}")
            return ai_response
            
        except Exception as e:
            # Update execution with error
            execution.status = HookStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            execution.execution_time = (execution.completed_at - execution.started_at).total_seconds()
            
            self.hook_stats["failed_responses"] += 1
            
            logger.error(f"Hook {event_type} failed for session {session_id}: {e}")
            
            # Send error notification
            await self._send_hook_error(session_id, event_type, str(e))
            
            return None
    
    async def on_run_hook(
        self, 
        session_id: str, 
        code: str, 
        language: str,
        context: Optional[AIContext] = None
    ) -> Optional[str]:
        """
        Trigger on_run hook when code execution starts
        
        Args:
            session_id: Session ID
            code: Code being executed
            language: Programming language
            context: Optional AI context
            
        Returns:
            Optional[str]: AI response
        """
        data = {
            "code": code,
            "language": language,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.trigger_hook(HookEventType.ON_RUN, session_id, data, context)
    
    async def on_error_hook(
        self, 
        session_id: str, 
        code: str, 
        language: str, 
        error: str,
        context: Optional[AIContext] = None
    ) -> Optional[str]:
        """
        Trigger on_error hook when code execution fails
        
        Args:
            session_id: Session ID
            code: Code that failed
            language: Programming language
            error: Error message
            context: Optional AI context
            
        Returns:
            Optional[str]: AI response
        """
        data = {
            "code": code,
            "language": language,
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.trigger_hook(HookEventType.ON_ERROR, session_id, data, context)
    
    async def on_save_hook(
        self, 
        session_id: str, 
        code: str, 
        language: str, 
        filename: str,
        context: Optional[AIContext] = None
    ) -> Optional[str]:
        """
        Trigger on_save hook when code is saved
        
        Args:
            session_id: Session ID
            code: Code being saved
            language: Programming language
            filename: Name of the file being saved
            context: Optional AI context
            
        Returns:
            Optional[str]: AI response
        """
        data = {
            "code": code,
            "language": language,
            "filename": filename,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return await self.trigger_hook(HookEventType.ON_SAVE, session_id, data, context)
    
    async def _send_ai_response(self, session_id: str, response: str, event_type: HookEventType):
        """Send AI response via WebSocket"""
        try:
            message = WebSocketMessage(
                type=WebSocketMessageType.GHOST_RESPONSE,
                session_id=session_id,
                data={
                    "response": response,
                    "hook_type": event_type.value,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            await connection_manager.send_to_session(session_id, message)
            
        except Exception as e:
            logger.error(f"Failed to send AI response via WebSocket: {e}")
    
    async def _send_hook_error(self, session_id: str, event_type: HookEventType, error: str):
        """Send hook error notification via WebSocket"""
        try:
            message = WebSocketMessage(
                type=WebSocketMessageType.ERROR,
                session_id=session_id,
                data={
                    "error": f"Hook {event_type.value} failed",
                    "detail": error,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            await connection_manager.send_to_session(session_id, message)
            
        except Exception as e:
            logger.error(f"Failed to send hook error via WebSocket: {e}")
    
    async def _call_event_listeners(
        self, 
        event_type: HookEventType, 
        event: HookEvent, 
        response: str
    ):
        """Call registered event listeners"""
        listeners = self.event_listeners.get(event_type, [])
        
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event, response)
                else:
                    listener(event, response)
            except Exception as e:
                logger.error(f"Event listener failed for {event_type}: {e}")
    
    def register_event_listener(self, event_type: HookEventType, listener: Callable):
        """
        Register a custom event listener for hook events
        
        Args:
            event_type: Type of hook event to listen for
            listener: Callback function to call when event occurs
        """
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        
        self.event_listeners[event_type].append(listener)
        logger.info(f"Registered event listener for {event_type}")
    
    def unregister_event_listener(self, event_type: HookEventType, listener: Callable):
        """
        Unregister an event listener
        
        Args:
            event_type: Type of hook event
            listener: Callback function to remove
        """
        if event_type in self.event_listeners:
            try:
                self.event_listeners[event_type].remove(listener)
                logger.info(f"Unregistered event listener for {event_type}")
            except ValueError:
                logger.warning(f"Event listener not found for {event_type}")
    
    def enable_hook(self, event_type: HookEventType):
        """Enable a specific hook type"""
        self.enabled_hooks[event_type] = True
        logger.info(f"Enabled hook {event_type}")
    
    def disable_hook(self, event_type: HookEventType):
        """Disable a specific hook type"""
        self.enabled_hooks[event_type] = False
        logger.info(f"Disabled hook {event_type}")
    
    def is_hook_enabled(self, event_type: HookEventType) -> bool:
        """Check if a hook type is enabled"""
        return self.enabled_hooks.get(event_type, False)
    
    def get_hook_executions(
        self, 
        session_id: Optional[str] = None,
        event_type: Optional[HookEventType] = None,
        limit: int = 100
    ) -> List[HookExecution]:
        """
        Get hook execution history
        
        Args:
            session_id: Filter by session ID
            event_type: Filter by event type
            limit: Maximum number of executions to return
            
        Returns:
            List[HookExecution]: List of hook executions
        """
        executions = list(self.hook_executions.values())
        
        # Apply filters
        if session_id:
            executions = [e for e in executions if e.event.session_id == session_id]
        
        if event_type:
            executions = [e for e in executions if e.event.event_type == event_type]
        
        # Sort by timestamp (newest first) and limit
        executions.sort(key=lambda x: x.started_at, reverse=True)
        return executions[:limit]
    
    def get_hook_statistics(self) -> Dict[str, Any]:
        """Get hook execution statistics"""
        return {
            **self.hook_stats,
            "enabled_hooks": {k.value: v for k, v in self.enabled_hooks.items()},
            "total_executions": len(self.hook_executions),
            "success_rate": (
                self.hook_stats["successful_responses"] / max(self.hook_stats["total_events"], 1)
            ) * 100
        }
    
    def clear_execution_history(self, older_than_hours: int = 24):
        """
        Clear old hook execution history
        
        Args:
            older_than_hours: Remove executions older than this many hours
        """
        cutoff_time = datetime.utcnow().timestamp() - (older_than_hours * 3600)
        
        executions_to_remove = [
            exec_id for exec_id, execution in self.hook_executions.items()
            if execution.started_at.timestamp() < cutoff_time
        ]
        
        for exec_id in executions_to_remove:
            del self.hook_executions[exec_id]
        
        logger.info(f"Cleared {len(executions_to_remove)} old hook executions")


# Global hook manager instance (will be initialized with Ghost AI service)
hook_manager: Optional[HookManagerService] = None


def get_hook_manager() -> Optional[HookManagerService]:
    """Get the global hook manager instance"""
    return hook_manager


def initialize_hook_manager(ghost_ai_service: GhostAIService) -> HookManagerService:
    """Initialize the global hook manager instance"""
    global hook_manager
    hook_manager = HookManagerService(ghost_ai_service)
    return hook_manager