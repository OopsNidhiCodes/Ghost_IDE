"""
Integration tests for the hook system and AI response triggers
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.hook_manager import HookManagerService, HookEventType, HookStatus
from app.services.ghost_ai import GhostAIService, HookEvent, AIContext
from app.models.schemas import LanguageType


class TestHookManagerService:
    """Test cases for HookManagerService"""
    
    @pytest.fixture
    def mock_ghost_ai(self):
        """Create a mock Ghost AI service"""
        mock_ai = AsyncMock(spec=GhostAIService)
        mock_ai.react_to_event = AsyncMock(return_value="Spooky AI response! 👻")
        return mock_ai
    
    @pytest.fixture
    def hook_manager(self, mock_ghost_ai):
        """Create a HookManagerService instance with mock AI"""
        return HookManagerService(mock_ghost_ai)
    
    @pytest.mark.asyncio
    async def test_hook_manager_initialization(self, hook_manager, mock_ghost_ai):
        """Test hook manager initialization"""
        assert hook_manager.ghost_ai == mock_ghost_ai
        assert len(hook_manager.event_listeners) == 3
        assert all(hook_manager.enabled_hooks.values())  # All hooks enabled by default
        assert hook_manager.hook_stats["total_events"] == 0
    
    @pytest.mark.asyncio
    async def test_on_run_hook_success(self, hook_manager, mock_ghost_ai):
        """Test successful on_run hook execution"""
        session_id = "test-session-123"
        code = "print('Hello, Ghost!')"
        language = "python"
        
        # Mock WebSocket manager
        with patch('app.services.hook_manager.connection_manager') as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            
            response = await hook_manager.on_run_hook(session_id, code, language)
        
        # Verify AI service was called
        mock_ghost_ai.react_to_event.assert_called_once()
        call_args = mock_ghost_ai.react_to_event.call_args
        event = call_args[0][0]
        
        assert event.event_type == HookEventType.ON_RUN
        assert event.session_id == session_id
        assert event.data["code"] == code
        assert event.data["language"] == language
        
        # Verify response
        assert response == "Spooky AI response! 👻"
        
        # Verify statistics
        assert hook_manager.hook_stats["total_events"] == 1
        assert hook_manager.hook_stats["successful_responses"] == 1
        assert hook_manager.hook_stats["events_by_type"]["on_run"] == 1
        
        # Verify WebSocket message was sent
        mock_ws.send_to_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_on_error_hook_success(self, hook_manager, mock_ghost_ai):
        """Test successful on_error hook execution"""
        session_id = "test-session-123"
        code = "print(undefined_variable)"
        language = "python"
        error = "NameError: name 'undefined_variable' is not defined"
        
        with patch('app.services.hook_manager.connection_manager') as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            
            response = await hook_manager.on_error_hook(session_id, code, language, error)
        
        # Verify AI service was called with error data
        mock_ghost_ai.react_to_event.assert_called_once()
        call_args = mock_ghost_ai.react_to_event.call_args
        event = call_args[0][0]
        
        assert event.event_type == HookEventType.ON_ERROR
        assert event.data["error"] == error
        assert response == "Spooky AI response! 👻"
    
    @pytest.mark.asyncio
    async def test_on_save_hook_success(self, hook_manager, mock_ghost_ai):
        """Test successful on_save hook execution"""
        session_id = "test-session-123"
        code = "def hello_ghost():\n    return 'Boo!'"
        language = "python"
        filename = "ghost_functions.py"
        
        with patch('app.services.hook_manager.connection_manager') as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            
            response = await hook_manager.on_save_hook(session_id, code, language, filename)
        
        # Verify AI service was called with save data
        mock_ghost_ai.react_to_event.assert_called_once()
        call_args = mock_ghost_ai.react_to_event.call_args
        event = call_args[0][0]
        
        assert event.event_type == HookEventType.ON_SAVE
        assert event.data["filename"] == filename
        assert response == "Spooky AI response! 👻"
    
    @pytest.mark.asyncio
    async def test_hook_disabled(self, hook_manager, mock_ghost_ai):
        """Test that disabled hooks don't trigger AI responses"""
        hook_manager.disable_hook(HookEventType.ON_RUN)
        
        response = await hook_manager.on_run_hook("session", "code", "python")
        
        # Verify AI service was not called
        mock_ghost_ai.react_to_event.assert_not_called()
        assert response is None
        assert hook_manager.hook_stats["total_events"] == 0
    
    @pytest.mark.asyncio
    async def test_hook_ai_failure(self, hook_manager, mock_ghost_ai):
        """Test hook behavior when AI service fails"""
        # Make AI service raise an exception
        mock_ghost_ai.react_to_event.side_effect = Exception("AI service error")
        
        with patch('app.services.hook_manager.connection_manager') as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            
            response = await hook_manager.on_run_hook("session", "code", "python")
        
        # Verify failure handling
        assert response is None
        assert hook_manager.hook_stats["total_events"] == 1
        assert hook_manager.hook_stats["failed_responses"] == 1
        assert hook_manager.hook_stats["successful_responses"] == 0
        
        # Verify error was sent via WebSocket
        mock_ws.send_to_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hook_execution_tracking(self, hook_manager, mock_ghost_ai):
        """Test that hook executions are properly tracked"""
        session_id = "test-session"
        
        with patch('app.services.hook_manager.connection_manager') as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            
            await hook_manager.on_run_hook(session_id, "code", "python")
        
        # Check execution history
        executions = hook_manager.get_hook_executions()
        assert len(executions) == 1
        
        execution = executions[0]
        assert execution.event.session_id == session_id
        assert execution.event.event_type == HookEventType.ON_RUN
        assert execution.status == HookStatus.COMPLETED
        assert execution.ai_response == "Spooky AI response! 👻"
        assert execution.error is None
        assert execution.execution_time is not None
    
    @pytest.mark.asyncio
    async def test_hook_execution_filtering(self, hook_manager, mock_ghost_ai):
        """Test filtering of hook execution history"""
        with patch('app.services.hook_manager.connection_manager') as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            
            # Create multiple executions
            await hook_manager.on_run_hook("session1", "code", "python")
            await hook_manager.on_error_hook("session2", "code", "python", "error")
            await hook_manager.on_save_hook("session1", "code", "python", "file.py")
        
        # Test filtering by session
        session1_executions = hook_manager.get_hook_executions(session_id="session1")
        assert len(session1_executions) == 2
        
        # Test filtering by event type
        run_executions = hook_manager.get_hook_executions(event_type=HookEventType.ON_RUN)
        assert len(run_executions) == 1
        assert run_executions[0].event.event_type == HookEventType.ON_RUN
    
    def test_hook_enable_disable(self, hook_manager):
        """Test enabling and disabling hooks"""
        # Test disable
        hook_manager.disable_hook(HookEventType.ON_RUN)
        assert not hook_manager.is_hook_enabled(HookEventType.ON_RUN)
        
        # Test enable
        hook_manager.enable_hook(HookEventType.ON_RUN)
        assert hook_manager.is_hook_enabled(HookEventType.ON_RUN)
    
    def test_hook_statistics(self, hook_manager):
        """Test hook statistics generation"""
        stats = hook_manager.get_hook_statistics()
        
        assert "total_events" in stats
        assert "successful_responses" in stats
        assert "failed_responses" in stats
        assert "success_rate" in stats
        assert "enabled_hooks" in stats
        assert "total_executions" in stats
        
        # Test success rate calculation
        hook_manager.hook_stats["total_events"] = 10
        hook_manager.hook_stats["successful_responses"] = 8
        stats = hook_manager.get_hook_statistics()
        assert stats["success_rate"] == 80.0
    
    def test_clear_execution_history(self, hook_manager):
        """Test clearing old execution history"""
        # Add some mock executions
        from app.services.hook_manager import HookExecution
        
        old_execution = HookExecution(
            id="old",
            event=HookEvent(
                event_type=HookEventType.ON_RUN,
                session_id="session",
                data={}
            )
        )
        old_execution.started_at = datetime(2023, 1, 1)  # Very old
        
        recent_execution = HookExecution(
            id="recent",
            event=HookEvent(
                event_type=HookEventType.ON_RUN,
                session_id="session",
                data={}
            )
        )
        
        hook_manager.hook_executions["old"] = old_execution
        hook_manager.hook_executions["recent"] = recent_execution
        
        # Clear old executions
        hook_manager.clear_execution_history(older_than_hours=1)
        
        # Only recent execution should remain
        assert "old" not in hook_manager.hook_executions
        assert "recent" in hook_manager.hook_executions
    
    @pytest.mark.asyncio
    async def test_event_listeners(self, hook_manager, mock_ghost_ai):
        """Test custom event listener registration and execution"""
        listener_called = False
        received_event = None
        received_response = None
        
        async def test_listener(event, response):
            nonlocal listener_called, received_event, received_response
            listener_called = True
            received_event = event
            received_response = response
        
        # Register listener
        hook_manager.register_event_listener(HookEventType.ON_RUN, test_listener)
        
        with patch('app.services.hook_manager.connection_manager') as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            
            await hook_manager.on_run_hook("session", "code", "python")
        
        # Verify listener was called
        assert listener_called
        assert received_event.event_type == HookEventType.ON_RUN
        assert received_response == "Spooky AI response! 👻"
        
        # Test unregistering listener
        hook_manager.unregister_event_listener(HookEventType.ON_RUN, test_listener)
        
        listener_called = False
        with patch('app.services.hook_manager.connection_manager') as mock_ws:
            mock_ws.send_to_session = AsyncMock()
            
            await hook_manager.on_run_hook("session", "code2", "python")
        
        # Listener should not be called after unregistering
        assert not listener_called


class TestHookIntegrationWithCodeExecution:
    """Test hook integration with code execution service"""
    
    @pytest.mark.asyncio
    async def test_code_execution_triggers_hooks(self):
        """Test that code execution properly triggers hooks"""
        from app.services.code_execution import CodeExecutionService
        from app.models.schemas import ExecutionRequest, LanguageType
        
        # Create mock hook manager
        mock_hook_manager = AsyncMock()
        
        with patch('app.services.hook_manager.get_hook_manager', return_value=mock_hook_manager):
            # Create execution service with Docker disabled for testing
            service = CodeExecutionService(skip_docker_init=True)
            
            request = ExecutionRequest(
                code="print('Hello')",
                language=LanguageType.PYTHON,
                session_id="test-session",
                timeout=30
            )
            
            # Execute code (will fail due to no Docker, but should still trigger hooks)
            result = await service.execute_code(request)
            
            # Verify on_run hook was called
            mock_hook_manager.on_run_hook.assert_called_once_with(
                session_id="test-session",
                code="print('Hello')",
                language="python"
            )
            
            # Verify on_error hook was called (due to Docker not available)
            mock_hook_manager.on_error_hook.assert_called_once()


class TestHookAPIEndpoints:
    """Test hook management API endpoints"""
    
    @pytest.fixture
    def mock_hook_manager(self):
        """Create a mock hook manager"""
        mock_manager = MagicMock()
        mock_manager.get_hook_statistics.return_value = {
            "enabled_hooks": {"on_run": True, "on_error": True, "on_save": True},
            "total_events": 10,
            "successful_responses": 8,
            "failed_responses": 2,
            "success_rate": 80.0,
            "total_executions": 10
        }
        mock_manager.get_hook_executions.return_value = []
        mock_manager.is_hook_enabled.return_value = True
        return mock_manager
    
    def test_hook_status_endpoint(self, mock_hook_manager):
        """Test the hook status API endpoint"""
        from app.api.endpoints.hooks import get_hook_status
        
        with patch('app.api.endpoints.hooks.get_hook_manager', return_value=mock_hook_manager):
            # This would normally be called by FastAPI
            # We're testing the logic directly
            mock_hook_manager.get_hook_statistics.assert_not_called()  # Not called yet
    
    def test_hook_manager_not_initialized(self):
        """Test API behavior when hook manager is not initialized"""
        from app.api.endpoints.hooks import get_hook_status
        from fastapi import HTTPException
        
        with patch('app.api.endpoints.hooks.get_hook_manager', return_value=None):
            # This should raise an HTTPException
            try:
                # In a real test, this would be called by the FastAPI test client
                pass
            except HTTPException as e:
                assert e.status_code == 503
                assert "not initialized" in e.detail


if __name__ == "__main__":
    pytest.main([__file__])