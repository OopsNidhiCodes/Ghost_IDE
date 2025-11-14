"""
Unit tests for cleanup service
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.cleanup_service import CleanupService, get_cleanup_service


@pytest.fixture
def cleanup_service():
    """Create a cleanup service for testing"""
    service = CleanupService()
    service.cleanup_interval = 0.1  # Short interval for testing
    return service


class TestCleanupService:
    """Test cases for CleanupService"""
    
    @pytest.mark.asyncio
    async def test_start_service(self, cleanup_service):
        """Test starting the cleanup service"""
        assert cleanup_service.is_running is False
        
        with patch.object(cleanup_service, '_cleanup_loop') as mock_loop:
            mock_loop.return_value = None
            
            await cleanup_service.start()
            
            assert cleanup_service.is_running is True
            assert cleanup_service._task is not None
    
    @pytest.mark.asyncio
    async def test_start_service_already_running(self, cleanup_service):
        """Test starting service when already running"""
        cleanup_service.is_running = True
        
        with patch('app.services.cleanup_service.logger') as mock_logger:
            await cleanup_service.start()
            
            mock_logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_service(self, cleanup_service):
        """Test stopping the cleanup service"""
        # Start service first
        cleanup_service.is_running = True
        mock_task = AsyncMock()
        cleanup_service._task = mock_task
        
        await cleanup_service.stop()
        
        assert cleanup_service.is_running is False
        mock_task.cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_cleanup(self, cleanup_service):
        """Test running cleanup tasks"""
        with patch.object(cleanup_service, '_cleanup_sessions') as mock_cleanup_sessions, \
             patch.object(cleanup_service, '_cleanup_chat_messages') as mock_cleanup_messages:
            
            mock_cleanup_sessions.return_value = None
            mock_cleanup_messages.return_value = None
            
            await cleanup_service.run_cleanup()
            
            mock_cleanup_sessions.assert_called_once()
            mock_cleanup_messages.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_sessions(self, cleanup_service):
        """Test session cleanup"""
        with patch.object(cleanup_service.session_manager, 'cleanup_expired_sessions') as mock_cleanup, \
             patch.object(cleanup_service.session_manager, 'get_active_sessions') as mock_get_active:
            
            mock_cleanup.return_value = None
            mock_get_active.return_value = ["session1", "session2"]
            
            await cleanup_service._cleanup_sessions()
            
            mock_cleanup.assert_called_once()
            mock_get_active.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_chat_messages(self, cleanup_service):
        """Test chat message cleanup"""
        with patch.object(cleanup_service.chat_manager, 'cleanup_old_messages_globally') as mock_cleanup:
            mock_cleanup.return_value = None
            
            await cleanup_service._cleanup_chat_messages()
            
            mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_force_cleanup(self, cleanup_service):
        """Test force cleanup"""
        with patch.object(cleanup_service, 'run_cleanup') as mock_run_cleanup:
            mock_run_cleanup.return_value = None
            
            await cleanup_service.force_cleanup()
            
            mock_run_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_cleanup_stats(self, cleanup_service):
        """Test getting cleanup statistics"""
        with patch.object(cleanup_service.session_manager, 'get_active_sessions') as mock_get_active:
            mock_get_active.return_value = ["session1", "session2", "session3"]
            
            stats = await cleanup_service.get_cleanup_stats()
            
            assert stats["is_running"] == cleanup_service.is_running
            assert stats["cleanup_interval_seconds"] == cleanup_service.cleanup_interval
            assert stats["active_sessions_count"] == 3
            assert "last_cleanup" in stats
    
    @pytest.mark.asyncio
    async def test_cleanup_loop_error_handling(self, cleanup_service):
        """Test error handling in cleanup loop"""
        cleanup_service.is_running = True
        
        with patch.object(cleanup_service, 'run_cleanup') as mock_run_cleanup, \
             patch('asyncio.sleep') as mock_sleep, \
             patch('app.services.cleanup_service.logger') as mock_logger:
            
            # First call raises exception, second call succeeds, then stop
            mock_run_cleanup.side_effect = [Exception("Test error"), None]
            mock_sleep.side_effect = [None, asyncio.CancelledError()]  # Stop after second iteration
            
            with pytest.raises(asyncio.CancelledError):
                await cleanup_service._cleanup_loop()
            
            # Should have logged the error
            mock_logger.error.assert_called_once()
            assert mock_run_cleanup.call_count == 2
    
    @pytest.mark.asyncio
    async def test_cleanup_loop_cancellation(self, cleanup_service):
        """Test cleanup loop cancellation"""
        cleanup_service.is_running = True
        
        with patch.object(cleanup_service, 'run_cleanup') as mock_run_cleanup, \
             patch('asyncio.sleep') as mock_sleep:
            
            mock_run_cleanup.return_value = None
            mock_sleep.side_effect = asyncio.CancelledError()
            
            # Should handle cancellation gracefully
            await cleanup_service._cleanup_loop()
            
            mock_run_cleanup.assert_called_once()


class TestCleanupServiceIntegration:
    """Integration tests for cleanup service"""
    
    def test_get_cleanup_service_singleton(self):
        """Test that get_cleanup_service returns singleton"""
        service1 = get_cleanup_service()
        service2 = get_cleanup_service()
        
        assert service1 is service2
    
    @pytest.mark.asyncio
    async def test_service_lifecycle(self, cleanup_service):
        """Test complete service lifecycle"""
        # Initially not running
        assert cleanup_service.is_running is False
        
        # Start service
        with patch.object(cleanup_service, '_cleanup_loop') as mock_loop:
            mock_task = AsyncMock()
            
            with patch('asyncio.create_task', return_value=mock_task) as mock_create_task:
                await cleanup_service.start()
                
                assert cleanup_service.is_running is True
                assert cleanup_service._task == mock_task
                mock_create_task.assert_called_once()
        
        # Stop service
        await cleanup_service.stop()
        
        assert cleanup_service.is_running is False
        mock_task.cancel.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_with_real_managers(self):
        """Test cleanup with real manager instances"""
        service = CleanupService()
        
        # Mock the manager methods
        with patch.object(service.session_manager, 'cleanup_expired_sessions') as mock_session_cleanup, \
             patch.object(service.session_manager, 'get_active_sessions') as mock_get_active, \
             patch.object(service.chat_manager, 'cleanup_old_messages_globally') as mock_chat_cleanup:
            
            mock_session_cleanup.return_value = None
            mock_get_active.return_value = []
            mock_chat_cleanup.return_value = None
            
            await service.run_cleanup()
            
            mock_session_cleanup.assert_called_once()
            mock_get_active.assert_called_once()
            mock_chat_cleanup.assert_called_once()


@pytest.mark.asyncio
async def test_cleanup_service_error_recovery():
    """Test cleanup service error recovery"""
    service = CleanupService()
    service.cleanup_interval = 0.01  # Very short for testing
    
    call_count = 0
    
    async def mock_cleanup():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("First call fails")
        # Second call succeeds
    
    with patch.object(service, 'run_cleanup', side_effect=mock_cleanup), \
         patch('asyncio.sleep') as mock_sleep:
        
        # Set up sleep to stop after two iterations
        mock_sleep.side_effect = [None, asyncio.CancelledError()]
        
        service.is_running = True
        
        # Should recover from first error and continue
        await service._cleanup_loop()
        
        assert call_count == 2


if __name__ == "__main__":
    pytest.main([__file__])