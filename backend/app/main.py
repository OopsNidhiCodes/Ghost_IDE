"""
GhostIDE Backend API
Main FastAPI application entry point
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app.api.routes import api_router
from app.api.endpoints import websocket
from app.services.ghost_ai import GhostAIService
from app.services.hook_manager import initialize_hook_manager
from app.services.cleanup_service import start_cleanup_service, stop_cleanup_service
from app.middleware.security import SecurityMiddleware
from app.middleware.auth import session_manager
from app.services.security_monitor import start_security_monitoring


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Ghost AI service
    openai_api_key = os.getenv("OPENAI_API_KEY", "test-key")
    ghost_ai_service = GhostAIService(api_key=openai_api_key)
    
    # Initialize Hook Manager
    hook_manager = initialize_hook_manager(ghost_ai_service)
    
    # Start cleanup service
    await start_cleanup_service()
    
    # Start security monitoring
    await start_security_monitoring()
    
    # Start session cleanup task
    import asyncio
    async def cleanup_sessions():
        while True:
            await asyncio.sleep(300)  # Clean up every 5 minutes
            session_manager.cleanup_expired_sessions()
    
    asyncio.create_task(cleanup_sessions())
    
    yield
    
    # Cleanup on shutdown
    await stop_cleanup_service()


# Create FastAPI application
app = FastAPI(
    title="GhostIDE API",
    description="Backend API for GhostIDE - A spooky online IDE with AI assistance",
    version="1.0.0",
    lifespan=lifespan
)

# Add security middleware (temporarily disabled for testing)
# app.add_middleware(SecurityMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Restrict methods
    allow_headers=["Content-Type", "Authorization", "X-Session-ID", "X-Requested-With"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Include WebSocket routes (no prefix needed for WebSocket endpoints)
app.include_router(websocket.router, tags=["websocket"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to GhostIDE API 👻"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "alive", "message": "The ghost is haunting successfully! 👻"}