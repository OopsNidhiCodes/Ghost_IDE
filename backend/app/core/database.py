"""
Database configuration and connection management
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    
    database_url: str = "sqlite+aiosqlite:///./ghostide.db"
    echo_sql: bool = False
    
    class Config:
        env_file = ".env"


# Initialize settings
db_settings = DatabaseSettings()

# Create async engine
engine = create_async_engine(
    db_settings.database_url,
    echo=db_settings.echo_sql,
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()