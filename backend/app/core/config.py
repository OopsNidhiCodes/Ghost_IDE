"""
Configuration settings for GhostIDE backend
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    database_url: str = "postgresql+asyncpg://ghost:spooky@localhost:5432/ghostide"
    
    # Redis settings
    redis_url: str = "redis://localhost:6379"
    
    # OpenAI API settings
    openai_api_key: Optional[str] = None
    
    # Ghost AI settings
    ghost_ai_model: str = "gpt-3.5-turbo"
    ghost_ai_temperature: float = 0.7
    ghost_ai_max_tokens: int = 500
    
    # Security settings
    secret_key: str = "your-secret-key-here"
    
    # CORS settings
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Code execution settings
    code_execution_timeout: int = 30
    max_concurrent_executions: int = 10
    
    # Session settings
    session_timeout_minutes: int = 60
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Global settings instance
settings = Settings()