"""
WebSocket message schemas and protocols
"""

from datetime import datetime
from typing import Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum

from app.models.schemas import ExecutionResult, ChatMessage


class WebSocketMessageType(str, Enum):
    """WebSocket message types"""
    # Connection management
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PING = "ping"
    PONG = "pong"
    
    # Client actions (sent from frontend)
    EXECUTE_CODE = "execute_code"
    GHOST_CHAT = "ghost_chat"
    SAVE_FILE = "save_file"
    HOOK_EVENT = "hook_event"
    
    # Code execution
    EXECUTION_START = "execution_start"
    EXECUTION_OUTPUT = "execution_output"
    EXECUTION_COMPLETE = "execution_complete"
    EXECUTION_ERROR = "execution_error"
    
    # Ghost AI
    AI_RESPONSE = "ai_response"
    AI_TYPING = "ai_typing"
    AI_ERROR = "ai_error"
    GHOST_RESPONSE = "ghost_response"  # Automated AI responses from hooks
    
    # Hook events
    HOOK_TRIGGERED = "hook_triggered"
    
    # Session management
    SESSION_UPDATE = "session_update"
    FILE_SAVED = "file_saved"
    
    # Errors
    ERROR = "error"


class WebSocketMessage(BaseModel):
    """Base WebSocket message structure"""
    type: WebSocketMessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class ConnectionMessage(WebSocketMessage):
    """Connection establishment message"""
    type: WebSocketMessageType = WebSocketMessageType.CONNECT
    session_id: str


class ExecutionStartMessage(WebSocketMessage):
    """Code execution start notification"""
    type: WebSocketMessageType = WebSocketMessageType.EXECUTION_START
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "language": "",
        "code_preview": ""  # First 100 chars of code
    })


class ExecutionOutputMessage(WebSocketMessage):
    """Streaming code execution output"""
    type: WebSocketMessageType = WebSocketMessageType.EXECUTION_OUTPUT
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "output": "",
        "stream": "stdout"  # stdout or stderr
    })


class ExecutionCompleteMessage(WebSocketMessage):
    """Code execution completion notification"""
    type: WebSocketMessageType = WebSocketMessageType.EXECUTION_COMPLETE
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "result": None,  # ExecutionResult dict
        "execution_id": ""
    })


class AIResponseMessage(WebSocketMessage):
    """Ghost AI response message"""
    type: WebSocketMessageType = WebSocketMessageType.AI_RESPONSE
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "message": None,  # ChatMessage dict
        "context": {}
    })


class AITypingMessage(WebSocketMessage):
    """Ghost AI typing indicator"""
    type: WebSocketMessageType = WebSocketMessageType.AI_TYPING
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "is_typing": True
    })


class HookTriggeredMessage(WebSocketMessage):
    """Hook event notification"""
    type: WebSocketMessageType = WebSocketMessageType.HOOK_TRIGGERED
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "hook_type": "",  # on_run, on_error, on_save
        "context": {}
    })


class GhostResponseMessage(WebSocketMessage):
    """Automated Ghost AI response from hooks"""
    type: WebSocketMessageType = WebSocketMessageType.GHOST_RESPONSE
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "response": "",
        "hook_type": "",  # on_run, on_error, on_save
        "timestamp": ""
    })


class SessionUpdateMessage(WebSocketMessage):
    """Session update notification"""
    type: WebSocketMessageType = WebSocketMessageType.SESSION_UPDATE
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "update_type": "",  # file_added, file_updated, preferences_changed
        "details": {}
    })


class ErrorMessage(WebSocketMessage):
    """Error notification"""
    type: WebSocketMessageType = WebSocketMessageType.ERROR
    data: Dict[str, Any] = Field(default_factory=lambda: {
        "error": "",
        "detail": "",
        "code": 500
    })


# Union type for all possible WebSocket messages
WebSocketMessageUnion = Union[
    ConnectionMessage,
    ExecutionStartMessage,
    ExecutionOutputMessage,
    ExecutionCompleteMessage,
    AIResponseMessage,
    AITypingMessage,
    HookTriggeredMessage,
    GhostResponseMessage,
    SessionUpdateMessage,
    ErrorMessage,
    WebSocketMessage
]