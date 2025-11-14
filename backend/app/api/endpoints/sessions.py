"""
Session management API endpoints
"""

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.schemas import (
    UserSession, UserSessionCreate, UserSessionUpdate,
    CodeFile, CodeFileCreate, CodeFileUpdate,
    SessionResponse, ErrorResponse
)
from app.services.session_manager import get_session_manager
from app.services.file_manager import get_file_manager
from app.services.chat_manager import get_chat_manager

router = APIRouter()

# Get service instances
session_manager = get_session_manager()
file_manager = get_file_manager()
chat_manager = get_chat_manager()


@router.post("/", response_model=SessionResponse)
async def create_session(session_data: UserSessionCreate):
    """Create a new user session"""
    try:
        session = await session_manager.create_session(session_data)
        
        return SessionResponse(
            success=True,
            message="Session created successfully! 👻",
            session=session
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """Get a user session by ID"""
    try:
        session = await session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        return SessionResponse(
            success=True,
            message="Session retrieved from the spirit world! 👻",
            session=session
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve session: {str(e)}"
        )


@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, session_update: UserSessionUpdate):
    """Update a user session"""
    try:
        session = await session_manager.update_session(session_id, session_update)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        return SessionResponse(
            success=True,
            message="Session updated in the ethereal plane! 👻",
            session=session
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update session: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a user session"""
    try:
        success = await session_manager.delete_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        return {"message": "Session banished to the shadow realm! 👻"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.post("/{session_id}/files", response_model=CodeFile)
async def create_file(session_id: str, file_data: CodeFileCreate):
    """Create a new code file in a session"""
    try:
        file = await file_manager.create_file(session_id, file_data)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        return file
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create file: {str(e)}"
        )


@router.get("/{session_id}/files", response_model=List[CodeFile])
async def get_session_files(session_id: str):
    """Get all files in a session"""
    try:
        return await file_manager.get_session_files(session_id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve files: {str(e)}"
        )


@router.put("/{session_id}/files/{file_id}", response_model=CodeFile)
async def update_file(session_id: str, file_id: str, file_update: CodeFileUpdate):
    """Update a code file and trigger on_save hook"""
    try:
        file = await file_manager.update_file(session_id, file_id, file_update)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in the spectral archives! 👻"
            )
        
        return file
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update file: {str(e)}"
        )


@router.post("/{session_id}/files/{file_id}/save")
async def save_file(session_id: str, file_id: str):
    """Explicitly save a file and trigger on_save hook"""
    try:
        file = await file_manager.save_file(session_id, file_id)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in the spectral archives! 👻"
            )
        
        return {
            "success": True,
            "message": f"File '{file.name}' saved to the ethereal realm! 👻",
            "file_id": file_id,
            "timestamp": file.last_modified.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )


@router.delete("/{session_id}/files/{file_id}")
async def delete_file(session_id: str, file_id: str):
    """Delete a code file from a session"""
    try:
        # Get file name before deletion
        file = await file_manager.get_file(session_id, file_id)
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in the spectral archives! 👻"
            )
        
        success = await file_manager.delete_file(session_id, file_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in the spectral archives! 👻"
            )
        
        return {
            "success": True,
            "message": f"File '{file.name}' banished to the void! 👻"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


# Session management and security endpoints

@router.post("/{session_id}/restore", response_model=SessionResponse)
async def restore_session(session_id: str):
    """Restore a session from persistent storage to active state"""
    try:
        session = await session_manager.restore_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        return SessionResponse(
            success=True,
            message="Session restored from the ethereal plane! 👻",
            session=session
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore session: {str(e)}"
        )


@router.get("/{session_id}/security")
async def get_session_security_info(session_id: str):
    """Get security information about a session"""
    try:
        security_info = await session_manager.get_session_security_info(session_id)
        
        if not security_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        return security_info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session security info: {str(e)}"
        )


@router.get("/{session_id}/validate")
async def validate_session(session_id: str):
    """Validate that a session exists and is accessible"""
    try:
        is_valid = await session_manager.validate_session(session_id)
        
        return {
            "session_id": session_id,
            "is_valid": is_valid,
            "message": "Session is haunting properly! 👻" if is_valid else "Session has vanished into the void! 👻"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate session: {str(e)}"
        )


# Chat management endpoints

@router.get("/{session_id}/chat")
async def get_chat_history(session_id: str, limit: int = 50, offset: int = 0):
    """Get chat history for a session"""
    try:
        messages = await chat_manager.get_session_messages(session_id, limit, offset)
        
        return {
            "session_id": session_id,
            "messages": messages,
            "count": len(messages)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.post("/{session_id}/chat")
async def add_chat_message(session_id: str, message: dict):
    """Add a message to chat history"""
    try:
        content = message.get("content", "")
        sender = message.get("sender", "user")
        context = message.get("context")
        
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Message content cannot be empty! 👻"
            )
        
        chat_message = await chat_manager.add_message(session_id, content, sender, context)
        
        if not chat_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        return chat_message
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add chat message: {str(e)}"
        )


@router.delete("/{session_id}/chat")
async def clear_chat_history(session_id: str):
    """Clear all chat history for a session"""
    try:
        success = await chat_manager.clear_session_history(session_id)
        
        return {
            "success": success,
            "message": "Chat history banished to the shadow realm! 👻"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear chat history: {str(e)}"
        )


@router.get("/{session_id}/chat/stats")
async def get_chat_stats(session_id: str):
    """Get statistics about a session's chat history"""
    try:
        stats = await chat_manager.get_session_stats(session_id)
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get chat stats: {str(e)}"
        )


# File management endpoints

@router.get("/{session_id}/files/{file_id}")
async def get_file(session_id: str, file_id: str):
    """Get a specific file"""
    try:
        file = await file_manager.get_file(session_id, file_id)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found in the spectral archives! 👻"
            )
        
        return file
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get file: {str(e)}"
        )


@router.post("/{session_id}/files/{file_id}/duplicate")
async def duplicate_file(session_id: str, file_id: str, new_name: str):
    """Duplicate an existing file with a new name"""
    try:
        file = await file_manager.duplicate_file(session_id, file_id, new_name)
        
        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original file not found in the spectral archives! 👻"
            )
        
        return file
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to duplicate file: {str(e)}"
        )


@router.get("/{session_id}/files/search")
async def search_files(session_id: str, query: str):
    """Search files by name or content"""
    try:
        files = await file_manager.search_files(session_id, query)
        
        return {
            "session_id": session_id,
            "query": query,
            "files": files,
            "count": len(files)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search files: {str(e)}"
        )


# Administrative endpoints

@router.get("/active")
async def get_active_sessions():
    """Get list of active session IDs (admin endpoint)"""
    try:
        active_sessions = await session_manager.get_active_sessions()
        
        return {
            "active_sessions": list(active_sessions),
            "count": len(active_sessions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get active sessions: {str(e)}"
        )


@router.post("/cleanup")
async def force_cleanup():
    """Force cleanup of expired sessions (admin endpoint)"""
    try:
        from app.services.cleanup_service import get_cleanup_service
        cleanup_service = get_cleanup_service()
        await cleanup_service.force_cleanup()
        
        return {"message": "Cleanup completed! Old sessions banished to the void! 👻"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run cleanup: {str(e)}"
        )


@router.get("/cleanup/stats")
async def get_cleanup_stats():
    """Get cleanup service statistics (admin endpoint)"""
    try:
        from app.services.cleanup_service import get_cleanup_service
        cleanup_service = get_cleanup_service()
        stats = await cleanup_service.get_cleanup_stats()
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cleanup stats: {str(e)}"
        )