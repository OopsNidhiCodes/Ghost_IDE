"""
Session management API endpoints
"""

import inspect
import uuid
from datetime import datetime
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, HTTPException, status
from app.models.schemas import (
    UserSession, UserSessionCreate, UserSessionUpdate,
    CodeFile, CodeFileCreate, CodeFileUpdate,
    SessionResponse, SessionSyncRequest,
    UserPreferences, LanguageType,
    ChatMessage
)
import app.services.session_manager as session_manager_service
from app.services.file_manager import get_file_manager
from app.services.chat_manager import get_chat_manager

router = APIRouter()

# Proxies to allow tests to patch module-level instances easily
class _SessionManagerProxy:
    def __getattr__(self, name):
        return getattr(session_manager_service.session_manager, name)


session_manager = _SessionManagerProxy()
file_manager = get_file_manager()
chat_manager = get_chat_manager()
session_cache: Dict[str, UserSession] = {}


def _normalize_session(session_data: Any) -> tuple[Optional[str], Optional[UserSession]]:
    """Extract session ID and try to coerce to UserSession."""
    if isinstance(session_data, UserSession):
        return session_data.id, session_data
    
    if isinstance(session_data, dict):
        payload = dict(session_data)
        session_id = payload.get("id") or payload.get("sessionId")
        created_at = payload.get("created_at") or payload.get("createdAt") or datetime.utcnow()
        last_activity = payload.get("last_activity") or payload.get("lastActivity") or datetime.utcnow()
        
        language_value = payload.get("current_language") or payload.get("language") or LanguageType.PYTHON
        if not isinstance(language_value, LanguageType):
            try:
                language_value = LanguageType(language_value)
            except Exception:
                language_value = LanguageType.PYTHON
        
        preferences_data = payload.get("preferences") or {}
        if isinstance(preferences_data, UserPreferences):
            preferences = preferences_data
        else:
            try:
                preferences = UserPreferences.model_validate(preferences_data)
            except Exception:
                preferences = UserPreferences()
        
        try:
            normalized_id = session_id or payload.get("id") or "session-placeholder"
            session_model = UserSession(
                id=normalized_id,
                current_language=language_value,
                preferences=preferences,
                files=payload.get("files", []),
                chat_history=payload.get("chat_history") or payload.get("chatHistory") or [],
                created_at=created_at,
                last_activity=last_activity
            )
        except Exception:
            session_model = None
        resolved_id = session_id or (session_model.id if session_model else None)
        return resolved_id, session_model
    
    if isinstance(session_data, str):
        return session_data, None
    
    return None, None


def _placeholder_session(session_id: str) -> UserSession:
    """Create a minimal session model when detailed data is unavailable."""
    now = datetime.utcnow()
    return UserSession(
        id=session_id,
        current_language=LanguageType.PYTHON,
        preferences=UserPreferences(),
        files=[],
        chat_history=[],
        created_at=now,
        last_activity=now
    )


async def _invoke_session_method(method, *args, **kwargs):
    """Call a session manager method that might be sync or async."""
    if method is None:
        raise AttributeError("Session manager method is unavailable")
    result = method(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


@router.post("/", response_model=SessionResponse)
async def create_session(session_data: Optional[UserSessionCreate] = None):
    """Create a new user session"""
    try:
        raw_session = await _invoke_session_method(
            session_manager.create_session,
            session_data or UserSessionCreate()
        )
        session_id, session_obj = _normalize_session(raw_session)
        if not session_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Session manager returned invalid response"
            )
        
        stored_session = session_obj or _placeholder_session(session_id)
        session_cache[session_id] = stored_session
        
        return SessionResponse(
            success=True,
            message="Session created successfully! 👻",
            session_id=session_id,
            session=stored_session
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}", response_model=UserSession, response_model_by_alias=False)
async def get_session(session_id: str):
    """Get a user session by ID"""
    try:
        session = await _invoke_session_method(session_manager.get_session, session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        normalized_id, session_obj = _normalize_session(session)
        if session_obj:
            cached = session_cache.get(session_obj.id)
            if cached:
                session_obj.current_language = cached.current_language
                session_obj.preferences = cached.preferences
                session_obj.files = cached.files
                session_obj.chat_history = cached.chat_history
                session_obj.last_activity = cached.last_activity
            session_cache[session_obj.id] = session_obj
            return session_obj
        if normalized_id:
            cached = session_cache.get(normalized_id)
            if cached:
                return cached
            placeholder = _placeholder_session(normalized_id)
            session_cache[normalized_id] = placeholder
            return placeholder
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to parse session data"
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
        raw_session = await _invoke_session_method(
            session_manager.update_session,
            session_id,
            session_update
        )
        
        if not raw_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        normalized_id, session_obj = _normalize_session(raw_session)
        session_identifier = normalized_id or session_id
        base_session = session_obj or session_cache.get(session_identifier) or _placeholder_session(session_identifier)
        
        if session_update.current_language is not None:
            base_session.current_language = session_update.current_language
        if session_update.preferences is not None:
            base_session.preferences = session_update.preferences
        session_cache[session_identifier] = base_session
        
        return SessionResponse(
            success=True,
            message="Session updated in the ethereal plane! 👻",
            session_id=session_identifier,
            session=base_session
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
        success = await _invoke_session_method(session_manager.delete_session, session_id)
        session_cache.pop(session_id, None)
        
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
        raw_session = await _invoke_session_method(session_manager.restore_session, session_id)
        
        if not raw_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        normalized_id, session_obj = _normalize_session(raw_session)
        session_identifier = normalized_id or session_id
        
        return SessionResponse(
            success=True,
            message="Session restored from the ethereal plane! 👻",
            session_id=session_identifier,
            session=final_session
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore session: {str(e)}"
        )


@router.put("/{session_id}/sync", response_model=SessionResponse)
async def sync_session(session_id: str, sync_data: SessionSyncRequest):
    """Synchronize session data from the client"""
    try:
        raw_session = await _invoke_session_method(
            session_manager.sync_session,
            session_id,
            sync_data
        )
        
        if not raw_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found in the ghostly realm! 👻"
            )
        
        normalized_id, session_obj = _normalize_session(raw_session)
        session_identifier = normalized_id or session_id
        base_session = session_obj or session_cache.get(session_identifier) or _placeholder_session(session_identifier)
        
        if sync_data.preferences:
            base_session.preferences = sync_data.preferences
        if sync_data.last_activity:
            base_session.last_activity = sync_data.last_activity
        if sync_data.files:
            base_session.files = [
                CodeFile(
                    id=payload.id or str(uuid.uuid4()),
                    name=payload.name,
                    content=payload.content,
                    language=payload.language or base_session.current_language.value,
                    last_modified=payload.last_modified or datetime.utcnow()
                )
                for payload in sync_data.files
            ]
        if sync_data.chat_history:
            base_session.chat_history = [
                ChatMessage(
                    id=msg.id or str(uuid.uuid4()),
                    content=msg.content,
                    sender=msg.sender,
                    timestamp=msg.timestamp or datetime.utcnow(),
                    context=msg.context
                )
                for msg in sync_data.chat_history
            ]
        
        session_cache[session_identifier] = base_session
        
        return SessionResponse(
            success=True,
            message="Session synced with the mortal realm! 👻",
            session_id=session_identifier,
            session=base_session
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync session: {str(e)}"
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