"""
Pydantic schemas for API request/response models
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


def to_camel(string: str) -> str:
    return "".join(word.capitalize() if i > 0 else word for i, word in enumerate(string.split("_")))


class LanguageType(str, Enum):
    """Supported programming languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    JAVA = "java"
    CPP = "cpp"
    C = "c"


class UserPreferences(BaseModel):
    """User preferences model"""
    theme: str = "ghost-dark"
    font_size: int = Field(default=14, ge=8, le=32, alias="fontSize")
    auto_save: bool = Field(default=True, alias="autoSave")
    auto_save_interval: int = Field(default=30, ge=5, le=300, alias="autoSaveInterval")  # seconds

    model_config = ConfigDict(populate_by_name=True)


class CodeFileBase(BaseModel):
    """Base model for code files"""
    name: str = Field(..., min_length=1, max_length=255)
    content: str = ""
    language: LanguageType

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class CodeFileCreate(CodeFileBase):
    """Model for creating a new code file"""
    pass


class CodeFileUpdate(BaseModel):
    """Model for updating a code file"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    language: Optional[LanguageType] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class CodeFile(CodeFileBase):
    """Complete code file model with metadata"""
    id: str
    last_modified: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True, alias_generator=to_camel)


class ChatMessage(BaseModel):
    """Chat message model"""
    id: str
    content: str
    sender: str  # 'user' or 'ghost'
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class UserSessionBase(BaseModel):
    """Base model for user sessions"""
    current_language: LanguageType = Field(default=LanguageType.PYTHON, alias="language")
    preferences: UserPreferences = UserPreferences()
    
    model_config = ConfigDict(populate_by_name=True)


class UserSessionCreate(UserSessionBase):
    """Model for creating a new user session"""
    pass


class UserSessionUpdate(BaseModel):
    """Model for updating a user session"""
    current_language: Optional[LanguageType] = None
    preferences: Optional[UserPreferences] = None


class UserSession(UserSessionBase):
    """Complete user session model"""
    id: str
    files: List[CodeFile] = []
    chat_history: List[ChatMessage] = []
    created_at: datetime
    last_activity: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class SyncFilePayload(BaseModel):
    """Payload for syncing files from clients"""
    id: Optional[str] = None
    name: str
    content: str = ""
    language: Optional[str] = None
    last_modified: Optional[datetime] = Field(default=None, alias="lastModified")

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class SyncChatMessage(BaseModel):
    """Payload for syncing chat history"""
    id: Optional[str] = None
    content: str
    sender: str
    timestamp: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class SessionSyncRequest(BaseModel):
    """Payload for syncing session data"""
    files: List[SyncFilePayload] = Field(default_factory=list)
    chat_history: List[SyncChatMessage] = Field(default_factory=list, alias="chatHistory")
    preferences: Optional[UserPreferences] = None
    last_activity: Optional[datetime] = Field(default=None, alias="lastActivity")

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class ExecutionRequest(BaseModel):
    """Model for code execution requests"""
    code: str = Field(..., min_length=1)
    language: LanguageType
    input: Optional[str] = None
    timeout: int = Field(default=30, ge=1, le=300)  # seconds
    session_id: str


class ExecutionResult(BaseModel):
    """Model for code execution results"""
    stdout: str
    stderr: str
    exit_code: int
    execution_time: float
    timed_out: bool = False

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class SessionResponse(BaseModel):
    """Response model for session operations"""
    success: bool
    message: str
    session_id: str = Field(alias="sessionId")
    session: Optional[UserSession] = None

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)