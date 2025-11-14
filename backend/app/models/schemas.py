"""
Pydantic schemas for API request/response models
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


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
    font_size: int = Field(default=14, ge=8, le=32)
    auto_save: bool = True
    auto_save_interval: int = Field(default=30, ge=5, le=300)  # seconds


class CodeFileBase(BaseModel):
    """Base model for code files"""
    name: str = Field(..., min_length=1, max_length=255)
    content: str = ""
    language: LanguageType


class CodeFileCreate(CodeFileBase):
    """Model for creating a new code file"""
    pass


class CodeFileUpdate(BaseModel):
    """Model for updating a code file"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    language: Optional[LanguageType] = None


class CodeFile(CodeFileBase):
    """Complete code file model with metadata"""
    id: str
    last_modified: datetime
    
    model_config = {"from_attributes": True}


class ChatMessage(BaseModel):
    """Chat message model"""
    id: str
    content: str
    sender: str  # 'user' or 'ghost'
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None


class UserSessionBase(BaseModel):
    """Base model for user sessions"""
    current_language: LanguageType = LanguageType.PYTHON
    preferences: UserPreferences = UserPreferences()


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
    
    model_config = {"from_attributes": True}


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


class SessionResponse(BaseModel):
    """Response model for session operations"""
    success: bool
    message: str
    session: Optional[UserSession] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)