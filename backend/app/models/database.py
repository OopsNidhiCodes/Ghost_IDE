"""
SQLAlchemy database models
"""

import uuid
from datetime import datetime
from typing import List
from sqlalchemy import String, Text, DateTime, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def generate_uuid():
    """Generate a new UUID string"""
    return str(uuid.uuid4())


class UserSessionDB(Base):
    """Database model for user sessions"""
    __tablename__ = "user_sessions"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    current_language: Mapped[str] = mapped_column(String(50), default="python")
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_activity: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    files: Mapped[List["CodeFileDB"]] = relationship(
        "CodeFileDB", 
        back_populates="session",
        cascade="all, delete-orphan"
    )
    chat_messages: Mapped[List["ChatMessageDB"]] = relationship(
        "ChatMessageDB",
        back_populates="session",
        cascade="all, delete-orphan"
    )


class CodeFileDB(Base):
    """Database model for code files"""
    __tablename__ = "code_files"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    last_modified: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("user_sessions.id"))
    
    # Relationships
    session: Mapped["UserSessionDB"] = relationship("UserSessionDB", back_populates="files")


class ChatMessageDB(Base):
    """Database model for chat messages"""
    __tablename__ = "chat_messages"
    
    id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sender: Mapped[str] = mapped_column(String(50), nullable=False)  # 'user' or 'ghost'
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    context: Mapped[dict] = mapped_column(JSON, nullable=True)
    session_id: Mapped[str] = mapped_column(String, ForeignKey("user_sessions.id"))
    
    # Relationships
    session: Mapped["UserSessionDB"] = relationship("UserSessionDB", back_populates="chat_messages")