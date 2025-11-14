"""
Integration tests for WebSocket-enabled services
"""

import json
import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.models.schemas import ExecutionRequest, LanguageType
from app.models.websocket_schemas import WebSocketMessageType


class TestWebSocketIntegration:
    """Test WebSocket integration with other services"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def session_id(self):
        """Test session ID"""
        return "test_integration_session"
    
    def test_websocket_execution_endpoint_http_only(self, client, session_id):
        """Test WebSocket-enabled code execution endpoint (HTTP response only)"""
        # Create execution request
        request_data = {
            "code": "print('Hello, WebSocket World!')",
            "language": LanguageType.PYTHON,
            "session_id": session_id,
            "timeout": 10
        }
        
        # Execute code via WebSocket-enabled endpoint
        response = client.post("/api/v1/execution/execute/websocket", json=request_data)
        
        # Check HTTP response
        assert response.status_code == 200
        result = response.json()
        assert "stdout" in result
        assert "stderr" in result
        assert "exit_code" in result
        assert "execution_time" in result
        
        # In test environment with mocked Docker, we expect an error message
        # but the endpoint should still work
        assert isinstance(result["exit_code"], int)
    
    def test_websocket_connection_stats(self, client, session_id):
        """Test WebSocket connection statistics"""
        # Check initial stats
        response = client.get("/ws/status")
        assert response.status_code == 200
        initial_stats = response.json()
        assert "total_connections" in initial_stats
        assert "active_sessions" in initial_stats
        assert "session_count" in initial_stats
        
        # Connect WebSocket
        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Check stats with active connection
            response = client.get("/ws/status")
            assert response.status_code == 200
            active_stats = response.json()
            
            # Should have at least one connection
            assert active_stats["total_connections"] >= 1
            assert session_id in active_stats["active_sessions"]
            
            # Check session-specific stats
            response = client.get(f"/ws/sessions/{session_id}/connections")
            assert response.status_code == 200
            session_stats = response.json()
            
            assert session_stats["session_id"] == session_id
            assert session_stats["connection_count"] >= 1
            assert session_stats["is_active"] is True
        
        # After disconnection, check stats again
        response = client.get(f"/ws/sessions/{session_id}/connections")
        assert response.status_code == 200
        final_stats = response.json()
        
        # Connection should be cleaned up
        assert final_stats["connection_count"] == 0
        assert final_stats["is_active"] is False
    
    def test_websocket_basic_communication(self, client, session_id):
        """Test basic WebSocket communication"""
        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == WebSocketMessageType.CONNECT
            assert message["session_id"] == session_id
            assert message["data"]["status"] == "connected"
            
            # Test ping/pong
            ping_message = {
                "type": WebSocketMessageType.PING,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {}
            }
            websocket.send_text(json.dumps(ping_message))
            
            # Should receive pong
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == WebSocketMessageType.PONG
            assert message["session_id"] == session_id


class TestMessageRouterUnit:
    """Unit tests for message router without WebSocket connections"""
    
    @pytest.fixture
    def mock_manager(self, monkeypatch):
        """Mock connection manager for isolated testing"""
        class MockManager:
            def __init__(self):
                self.sent_messages = []
            
            async def send_to_session(self, session_id: str, message):
                self.sent_messages.append((session_id, message))
            
            async def send_session_error(self, session_id: str, error: str, detail: str = "", code: int = 500):
                self.sent_messages.append((session_id, f"ERROR: {error}"))
        
        mock = MockManager()
        return mock
    
    @pytest.fixture
    def router(self, mock_manager):
        """Create message router with mocked manager"""
        from app.services.message_router import MessageRouter
        router = MessageRouter()
        router.manager = mock_manager
        return router
    
    @pytest.mark.asyncio
    async def test_execution_notifications(self, router, mock_manager):
        """Test execution notification methods"""
        session_id = "test_session"
        
        # Test execution start
        await router.notify_execution_start(session_id, "python", "print('hello')")
        assert len(mock_manager.sent_messages) == 1
        
        # Test execution output streaming
        await router.stream_execution_output(session_id, "Hello World!", "stdout")
        assert len(mock_manager.sent_messages) == 2
        
        # Test execution complete
        from app.models.schemas import ExecutionResult
        result = ExecutionResult(
            stdout="Hello World!",
            stderr="",
            exit_code=0,
            execution_time=1.0
        )
        await router.notify_execution_complete(session_id, result)
        assert len(mock_manager.sent_messages) == 3
        
        # Verify message types
        _, start_msg = mock_manager.sent_messages[0]
        _, output_msg = mock_manager.sent_messages[1]
        _, complete_msg = mock_manager.sent_messages[2]
        
        assert start_msg.type == WebSocketMessageType.EXECUTION_START
        assert output_msg.type == WebSocketMessageType.EXECUTION_OUTPUT
        assert complete_msg.type == WebSocketMessageType.EXECUTION_COMPLETE
    
    @pytest.mark.asyncio
    async def test_ai_notifications(self, router, mock_manager):
        """Test AI notification methods"""
        session_id = "test_session"
        
        # Test AI typing indicator
        await router.set_ai_typing(session_id, True)
        assert len(mock_manager.sent_messages) == 1
        
        # Test AI response
        from app.models.schemas import ChatMessage
        chat_msg = ChatMessage(
            id="msg_123",
            content="Hello from Ghost AI!",
            sender="ghost",
            timestamp=datetime.utcnow()
        )
        await router.send_ai_response(session_id, chat_msg)
        assert len(mock_manager.sent_messages) == 2
        
        # Verify message types
        _, typing_msg = mock_manager.sent_messages[0]
        _, ai_msg = mock_manager.sent_messages[1]
        
        assert typing_msg.type == WebSocketMessageType.AI_TYPING
        assert ai_msg.type == WebSocketMessageType.AI_RESPONSE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])