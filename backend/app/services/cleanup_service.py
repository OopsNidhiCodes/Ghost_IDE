"""
Background cleanup service for session management and garbage collection
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.services.session_manager import get_session_manager
from app.services.chat_manager import get_chat_manager


logger = logging.getLogger(__name__)


class CleanupService:
    """Background service for cleaning up expired sessions and old data"""
    
    def __init__(self):
        self.session_manager = get_session_manager()
        self.chat_manager = get_chat_manager()
        self.cleanup_interval = 3600  # 1 hour
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the cleanup service"""
        if self.is_running:
            logger.warning("Cleanup service is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._cleanup_loop())
        logger.info("Cleanup service started")
    
    async def stop(self):
        """Stop the cleanup service"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Cleanup service stopped")
    
    async def _cleanup_loop(self):
        """Main cleanup loop"""
        while self.is_running:
            try:
                await self.run_cleanup()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def run_cleanup(self):
        """Run all cleanup tasks"""
        logger.info("Starting cleanup tasks")
        
        try:
            # Clean up expired sessions
            await self._cleanup_sessions()
            
            # Clean up old chat messages
            await self._cleanup_chat_messages()
            
            # Log cleanup completion
            logger.info("Cleanup tasks completed successfully")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def _cleanup_sessions(self):
        """Clean up expired and old sessions"""
        try:
            # Clean up expired Redis sessions and old PostgreSQL sessions
            await self.session_manager.cleanup_expired_sessions()
            
            # Get active session count for logging
            active_sessions = await self.session_manager.get_active_sessions()
            logger.info(f"Active sessions after cleanup: {len(active_sessions)}")
            
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {e}")
    
    async def _cleanup_chat_messages(self):
        """Clean up old chat messages"""
        try:
            await self.chat_manager.cleanup_old_messages_globally()
            logger.info("Old chat messages cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up chat messages: {e}")
    
    async def force_cleanup(self):
        """Force an immediate cleanup run"""
        logger.info("Force cleanup requested")
        await self.run_cleanup()
    
    async def get_cleanup_stats(self) -> dict:
        """Get statistics about the cleanup service"""
        active_sessions = await self.session_manager.get_active_sessions()
        
        return {
            "is_running": self.is_running,
            "cleanup_interval_seconds": self.cleanup_interval,
            "active_sessions_count": len(active_sessions),
            "last_cleanup": datetime.utcnow().isoformat(),
            "next_cleanup_in_seconds": self.cleanup_interval if self.is_running else None
        }


# Global cleanup service instance
_cleanup_service: Optional[CleanupService] = None


def get_cleanup_service() -> CleanupService:
    """Get the global cleanup service instance"""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = CleanupService()
    return _cleanup_service


async def start_cleanup_service():
    """Start the background cleanup service"""
    cleanup_service = get_cleanup_service()
    await cleanup_service.start()


async def stop_cleanup_service():
    """Stop the background cleanup service"""
    cleanup_service = get_cleanup_service()
    await cleanup_service.stop()