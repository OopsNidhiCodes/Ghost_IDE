"""
Configuration settings for GhostIDE backend
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    database_url: str = "sqlite+aiosqlite:///./ghost_ide.db"
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # OpenAI API settings
    openai_api_key: Optional[str] = "test-key"
    
    # Ghost AI settings
    ghost_ai_model: str = "gpt-3.5-turbo"
    ghost_ai_temperature: float = 0.7
    ghost_ai_max_tokens: int = 500
    
    # Security settings
    secret_key: str = "dev-secret-key-change-in-production"
    
    # CORS settings
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"]
    
    # Code execution settings
    code_execution_timeout: int = 30
    max_concurrent_executions: int = 10
    
    # Session settings
    session_timeout_minutes: int = 60
    
    # Development settings
    debug: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env file


# Global settings instance
settings = Settings()