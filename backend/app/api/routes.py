"""
Main API router that includes all route modules
"""

from fastapi import APIRouter
from app.api.endpoints import sessions, execution, ghost_ai, hooks, languages, security

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(execution.router, prefix="/execution", tags=["execution"])
api_router.include_router(ghost_ai.router, prefix="/ghost", tags=["ghost-ai"])
api_router.include_router(hooks.router, prefix="/hooks", tags=["hooks"])
api_router.include_router(languages.router, tags=["languages"])
api_router.include_router(security.router, prefix="/security", tags=["security"])