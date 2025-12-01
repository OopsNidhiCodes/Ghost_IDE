"""
Ghost AI API endpoints
"""

import logging
from datetime import datetime
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.services.ghost_ai import (
    GhostAIService, 
    AIContext, 
    CodeGenerationRequest,
    HookEvent,
    GhostPersonality,
    get_ghost_ai_service as core_get_ghost_ai_service
)
from app.models.schemas import LanguageType
from app.core.config import settings
from app.middleware.auth import get_current_session, require_valid_session
from app.middleware.security import security_logger, input_validator

logger = logging.getLogger(__name__)

router = APIRouter()

class ChatRequest(BaseModel):
    """Request model for chat with Ghost AI"""
    message: str
    session_id: str
    context: AIContext


class ChatResponse(BaseModel):
    """Response model for Ghost AI chat"""
    response: str
    timestamp: str


class HookEventRequest(BaseModel):
    """Request model for hook events"""
    event: HookEvent
    context: AIContext


@router.post("/chat/{session_id}")
async def chat_with_ghost(session_id: str, request: Dict[str, Any]):
    """
    Chat with the Ghost AI assistant (simplified for testing)
    """
    try:
        message = request.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        context_payload = request.get("context") or {}
        if isinstance(context_payload, dict):
            context = AIContext(**context_payload)
        elif isinstance(context_payload, AIContext):
            context = context_payload
        else:
            context = AIContext()
        
        ghost_service = core_get_ghost_ai_service()
        response = await ghost_service.generate_response(message, context)
        
        return {
            "message": response,
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in ghost chat: {e}")
        raise HTTPException(
            status_code=500,
            detail="The ghost is temporarily unavailable... 👻"
        )


@router.post("/hook-event", response_model=ChatResponse)
async def handle_hook_event(
    request: HookEventRequest,
    ghost_service: GhostAIService = Depends(core_get_ghost_ai_service)
):
    """
    Handle hook events and get Ghost AI reactions
    """
    try:
        response = await ghost_service.react_to_event(
            event=request.event,
            context=request.context
        )
        
        return ChatResponse(
            response=response,
            timestamp=str(datetime.utcnow())
        )
        
    except Exception as e:
        logger.error(f"Error handling hook event: {e}")
        raise HTTPException(
            status_code=500,
            detail="The spirits are restless... 👻"
        )


@router.post("/generate-code")
async def generate_code_snippet(
    request: CodeGenerationRequest,
    ghost_service: GhostAIService = Depends(core_get_ghost_ai_service)
):
    """
    Generate spooky code snippets
    """
    try:
        code = await ghost_service.generate_code_snippet(request)
        
        return {
            "code": code,
            "language": request.language,
            "spooky_level": request.spooky_level
        }
        
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        raise HTTPException(
            status_code=500,
            detail="The code spirits are having trouble manifesting... 👻"
        )


@router.get("/personality")
async def get_personality(
    ghost_service: GhostAIService = Depends(core_get_ghost_ai_service)
):
    """
    Get current Ghost AI personality configuration
    """
    try:
        return ghost_service.get_personality_info()
        
    except Exception as e:
        logger.error(f"Error getting personality: {e}")
        raise HTTPException(
            status_code=500,
            detail="The ghost's identity is shrouded in mystery... 👻"
        )


@router.put("/personality")
async def update_personality(
    personality: GhostPersonality,
    ghost_service: GhostAIService = Depends(core_get_ghost_ai_service)
):
    """
    Update Ghost AI personality configuration
    """
    try:
        ghost_service.update_personality(personality)
        
        return {
            "message": f"Ghost personality updated to {personality.name}",
            "personality": ghost_service.get_personality_info()
        }
        
    except Exception as e:
        logger.error(f"Error updating personality: {e}")
        raise HTTPException(
            status_code=500,
            detail="The ghost resists personality changes... 👻"
        )


@router.get("/health")
async def ghost_health_check(
    ghost_service: GhostAIService = Depends(core_get_ghost_ai_service)
):
    """
    Check if Ghost AI service is operational
    """
    try:
        # Simple test to verify the service is working
        test_context = AIContext()
        test_response = await ghost_service.generate_response(
            "Say hello briefly", 
            test_context
        )
        
        return {
            "status": "haunting",
            "message": "Ghost AI is operational 👻",
            "test_response": test_response[:100] + "..." if len(test_response) > 100 else test_response
        }
        
    except Exception as e:
        logger.error(f"Ghost AI health check failed: {e}")
        return {
            "status": "exorcised",
            "message": "Ghost AI is temporarily unavailable 💀",
            "error": str(e)
        }