"""
Hook management API endpoints
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.hook_manager import get_hook_manager, HookEventType
from app.services.ghost_ai import HookEvent

logger = logging.getLogger(__name__)

router = APIRouter()


class HookStatusResponse(BaseModel):
    """Response model for hook status"""
    enabled_hooks: Dict[str, bool]
    total_events: int
    successful_responses: int
    failed_responses: int
    success_rate: float


class HookExecutionResponse(BaseModel):
    """Response model for hook execution"""
    id: str
    event_type: str
    session_id: str
    status: str
    ai_response: Optional[str]
    error: Optional[str]
    started_at: str
    completed_at: Optional[str]
    execution_time: Optional[float]


class HookToggleRequest(BaseModel):
    """Request model for enabling/disabling hooks"""
    event_type: HookEventType
    enabled: bool


@router.get("/status", response_model=HookStatusResponse)
async def get_hook_status():
    """Get current hook system status and statistics"""
    hook_manager = get_hook_manager()
    if not hook_manager:
        raise HTTPException(status_code=503, detail="Hook manager not initialized")
    
    stats = hook_manager.get_hook_statistics()
    
    return HookStatusResponse(
        enabled_hooks=stats["enabled_hooks"],
        total_events=stats["total_events"],
        successful_responses=stats["successful_responses"],
        failed_responses=stats["failed_responses"],
        success_rate=stats["success_rate"]
    )


@router.get("/executions", response_model=List[HookExecutionResponse])
async def get_hook_executions(
    session_id: Optional[str] = Query(None, description="Filter by session ID"),
    event_type: Optional[HookEventType] = Query(None, description="Filter by event type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of executions to return")
):
    """Get hook execution history"""
    hook_manager = get_hook_manager()
    if not hook_manager:
        raise HTTPException(status_code=503, detail="Hook manager not initialized")
    
    executions = hook_manager.get_hook_executions(
        session_id=session_id,
        event_type=event_type,
        limit=limit
    )
    
    return [
        HookExecutionResponse(
            id=execution.id,
            event_type=execution.event.event_type.value,
            session_id=execution.event.session_id,
            status=execution.status.value,
            ai_response=execution.ai_response,
            error=execution.error,
            started_at=execution.started_at.isoformat(),
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
            execution_time=execution.execution_time
        )
        for execution in executions
    ]


@router.post("/toggle")
async def toggle_hook(request: HookToggleRequest):
    """Enable or disable a specific hook type"""
    hook_manager = get_hook_manager()
    if not hook_manager:
        raise HTTPException(status_code=503, detail="Hook manager not initialized")
    
    if request.enabled:
        hook_manager.enable_hook(request.event_type)
    else:
        hook_manager.disable_hook(request.event_type)
    
    return {
        "success": True,
        "message": f"Hook {request.event_type.value} {'enabled' if request.enabled else 'disabled'}",
        "event_type": request.event_type.value,
        "enabled": request.enabled
    }


@router.post("/enable/{event_type}")
async def enable_hook(event_type: HookEventType):
    """Enable a specific hook type"""
    hook_manager = get_hook_manager()
    if not hook_manager:
        raise HTTPException(status_code=503, detail="Hook manager not initialized")
    
    hook_manager.enable_hook(event_type)
    
    return {
        "success": True,
        "message": f"Hook {event_type.value} enabled",
        "event_type": event_type.value,
        "enabled": True
    }


@router.post("/disable/{event_type}")
async def disable_hook(event_type: HookEventType):
    """Disable a specific hook type"""
    hook_manager = get_hook_manager()
    if not hook_manager:
        raise HTTPException(status_code=503, detail="Hook manager not initialized")
    
    hook_manager.disable_hook(event_type)
    
    return {
        "success": True,
        "message": f"Hook {event_type.value} disabled",
        "event_type": event_type.value,
        "enabled": False
    }


@router.get("/enabled/{event_type}")
async def is_hook_enabled(event_type: HookEventType):
    """Check if a specific hook type is enabled"""
    hook_manager = get_hook_manager()
    if not hook_manager:
        raise HTTPException(status_code=503, detail="Hook manager not initialized")
    
    enabled = hook_manager.is_hook_enabled(event_type)
    
    return {
        "event_type": event_type.value,
        "enabled": enabled
    }


@router.delete("/executions")
async def clear_execution_history(
    older_than_hours: int = Query(24, ge=1, le=168, description="Clear executions older than this many hours")
):
    """Clear old hook execution history"""
    hook_manager = get_hook_manager()
    if not hook_manager:
        raise HTTPException(status_code=503, detail="Hook manager not initialized")
    
    hook_manager.clear_execution_history(older_than_hours)
    
    return {
        "success": True,
        "message": f"Cleared hook executions older than {older_than_hours} hours"
    }


@router.post("/test/{event_type}")
async def test_hook(
    event_type: HookEventType,
    session_id: str = Query(..., description="Session ID for testing"),
    code: str = Query("print('Hello, Ghost!')", description="Test code"),
    language: str = Query("python", description="Programming language")
):
    """Test a hook by manually triggering it"""
    hook_manager = get_hook_manager()
    if not hook_manager:
        raise HTTPException(status_code=503, detail="Hook manager not initialized")
    
    try:
        # Prepare test data based on hook type
        if event_type == HookEventType.ON_RUN:
            response = await hook_manager.on_run_hook(session_id, code, language)
        elif event_type == HookEventType.ON_ERROR:
            test_error = "Test error: Division by zero"
            response = await hook_manager.on_error_hook(session_id, code, language, test_error)
        elif event_type == HookEventType.ON_SAVE:
            filename = "test_file.py"
            response = await hook_manager.on_save_hook(session_id, code, language, filename)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown hook type: {event_type}")
        
        return {
            "success": True,
            "message": f"Hook {event_type.value} tested successfully",
            "event_type": event_type.value,
            "ai_response": response,
            "session_id": session_id
        }
        
    except Exception as e:
        logger.error(f"Failed to test hook {event_type}: {e}")
        raise HTTPException(status_code=500, detail=f"Hook test failed: {str(e)}")