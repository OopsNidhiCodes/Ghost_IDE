"""
Integration tests for WebSocket communication
"""

import json
import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI
from datetime import datetime
from typing import List, Dict, Any

from app.main import app
from app.services.websocket_manager import connection_manager
from app.services.message_router import message_router
from app.models.websocket_schemas import (
    WebSocketMessage,
    WebSocketMessageType,
    ExecutionStartMessage,
    ExecutionOutputMessage,
    ExecutionCompleteMessage,
    AIResponseMessage,
    AITypingMessage
)
from app.models.schemas import ExecutionResult, ChatMessage


class TestWebSocketCommunication:
    """Test WebSocket communication functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def session_id(self):
        """Test session ID"""
        return "test_session_123"
    
    def test_websocket_status_endpoint(self, client):
        """Test WebSocket status endpoint"""
        response = client.get("/ws/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_connections" in data
        assert "active_sessions" in data
        assert "session_count" in data
        assert isinstance(data["total_connections"], int)
        assert isinstance(data["active_sessions"], list)
        assert isinstance(data["session_count"], int)
    
    def test_session_connections_endpoint(self, client, session_id):
        """Test session connections endpoint"""
        response = client.get(f"/ws/sessions/{session_id}/connections")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert "connection_count" in data
        assert "is_active" in data
        assert isinstance(data["connection_count"], int)
        assert isinstance(data["is_active"], bool)
    
    def test_websocket_connection_basic(self, client, session_id):
        """Test basic WebSocket connection"""
        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Should receive connection confirmation
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == WebSocketMessageType.CONNECT
            assert message["session_id"] == session_id
            assert message["data"]["status"] == "connected"
            assert "connection_id" in message["data"]
    
    def test_websocket_ping_pong(self, client, session_id):
        """Test WebSocket ping/pong functionality"""
        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send ping
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
            assert "timestamp" in message["data"]
    
    def test_websocket_invalid_json(self, client, session_id):
        """Test WebSocket handling of invalid JSON"""
        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send invalid JSON
            websocket.send_text("invalid json {")
            
            # Should receive error message
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == WebSocketMessageType.ERROR
            assert "Invalid message format" in message["data"]["error"]
    
    def test_websocket_echo_message(self, client, session_id):
        """Test WebSocket echo functionality"""
        with client.websocket_connect(f"/ws/{session_id}") as websocket:
            # Skip connection message
            websocket.receive_text()
            
            # Send test message with valid enum type
            test_message = {
                "type": WebSocketMessageType.SESSION_UPDATE,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": {"test": "data"}
            }
            websocket.send_text(json.dumps(test_message))
            
            # Should receive echo
            data = websocket.receive_text()
            message = json.loads(data)
            
            assert message["type"] == WebSocketMessageType.SESSION_UPDATE
            assert message["session_id"] == session_id
            assert message["data"]["echo"] is True
            assert message["data"]["original_message"] == {"test": "data"}


class TestConnectionManager:
    """Test WebSocket connection manager"""
    
    @pytest.fixture
    def manager(self):
        """Create fresh connection manager for testing"""
        from app.services.websocket_manager import ConnectionManager
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        class MockWebSocket:
            def __init__(self):
                self.messages = []
                self.closed = False
            
            async def accept(self):
                pass
            
            async def send_text(self, data: str):
                if not self.closed:
                    self.messages.append(data)
            
            def close(self):
                self.closed = True
        
        return MockWebSocket()
    
    @pytest.mark.asyncio
    async def test_connection_manager_connect(self, manager, mock_websocket):
        """Test connection manager connect functionality"""
        session_id = "test_session"
        
        # Connect websocket
        result = await manager.connect(mock_websocket, session_id)
        assert result is True
        
        # Check connection is tracked
        assert session_id in manager.active_connections
        assert mock_websocket in manager.active_connections[session_id]
        assert manager.connection_sessions[mock_websocket] == session_id
        
        # Check connection confirmation was sent
        assert len(mock_websocket.messages) == 1
        message = json.loads(mock_websocket.messages[0])
        assert message["type"] == WebSocketMessageType.CONNECT
    
    @pytest.mark.asyncio
    async def test_connection_manager_disconnect(self, manager, mock_websocket):
        """Test connection manager disconnect functionality"""
        session_id = "test_session"
        
        # Connect first
        await manager.connect(mock_websocket, session_id)
        
        # Disconnect
        await manager.disconnect(mock_websocket)
        
        # Check connection is removed
        assert session_id not in manager.active_connections
        assert mock_websocket not in manager.connection_sessions
    
    @pytest.mark.asyncio
    async def test_connection_manager_send_to_session(self, manager, mock_websocket):
        """Test sending messages to session"""
        session_id = "test_session"
        
        # Connect websocket
        await manager.connect(mock_websocket, session_id)
        mock_websocket.messages.clear()  # Clear connection message
        
        # Send message to session
        test_message = WebSocketMessage(
            type=WebSocketMessageType.PING,
            session_id=session_id,
            data={"test": "data"}
        )
        await manager.send_to_session(session_id, test_message)
        
        # Check message was sent
        assert len(mock_websocket.messages) == 1
        message = json.loads(mock_websocket.messages[0])
        assert message["type"] == WebSocketMessageType.PING
        assert message["session_id"] == session_id
    
    def test_connection_manager_stats(self, manager):
        """Test connection manager statistics"""
        # Initially empty
        assert manager.get_total_connections() == 0
        assert manager.get_active_sessions() == []
        
        # Add some mock data
        manager.active_connections["session1"] = ["ws1", "ws2"]
        manager.active_connections["session2"] = ["ws3"]
        
        assert manager.get_total_connections() == 3
        assert set(manager.get_active_sessions()) == {"session1", "session2"}
        assert manager.get_session_connection_count("session1") == 2
        assert manager.get_session_connection_count("session2") == 1
        assert manager.get_session_connection_count("nonexistent") == 0


class TestMessageRouter:
    """Test message router functionality"""
    
    @pytest.fixture
    def router(self, mock_manager):
        """Create message router for testing"""
        from app.services.message_router import MessageRouter
        router = MessageRouter()
        router.manager = mock_manager  # Replace the manager with our mock
        return router
    
    @pytest.fixture
    def mock_manager(self, monkeypatch):
        """Mock connection manager"""
        class MockManager:
            def __init__(self):
                self.sent_messages = []
            
            async def send_to_session(self, session_id: str, message):
                self.sent_messages.append((session_id, message))
            
            async def send_session_error(self, session_id: str, error: str, detail: str = "", code: int = 500):
                self.sent_messages.append((session_id, f"ERROR: {error}"))
        
        mock = MockManager()
        # Patch both the import in message_router and the router's manager attribute
        monkeypatch.setattr("app.services.message_router.connection_manager", mock)
        return mock
    
    @pytest.mark.asyncio
    async def test_notify_execution_start(self, router, mock_manager):
        """Test execution start notification"""
        session_id = "test_session"
        language = "python"
        code_preview = "print('hello world')"
        
        await router.notify_execution_start(session_id, language, code_preview)
        
        assert len(mock_manager.sent_messages) == 1
        session, message = mock_manager.sent_messages[0]
        assert session == session_id
        assert message.type == WebSocketMessageType.EXECUTION_START
        assert message.data["language"] == language
        assert message.data["code_preview"] == code_preview
    
    @pytest.mark.asyncio
    async def test_stream_execution_output(self, router, mock_manager):
        """Test execution output streaming"""
        session_id = "test_session"
        output = "Hello, World!"
        stream = "stdout"
        
        await router.stream_execution_output(session_id, output, stream)
        
        assert len(mock_manager.sent_messages) == 1
        session, message = mock_manager.sent_messages[0]
        assert session == session_id
        assert message.type == WebSocketMessageType.EXECUTION_OUTPUT
        assert message.data["output"] == output
        assert message.data["stream"] == stream
    
    @pytest.mark.asyncio
    async def test_notify_execution_complete(self, router, mock_manager):
        """Test execution complete notification"""
        session_id = "test_session"
        result = ExecutionResult(
            stdout="Hello, World!",
            stderr="",
            exit_code=0,
            execution_time=1.5
        )
        
        await router.notify_execution_complete(session_id, result)
        
        assert len(mock_manager.sent_messages) == 1
        session, message = mock_manager.sent_messages[0]
        assert session == session_id
        assert message.type == WebSocketMessageType.EXECUTION_COMPLETE
        assert message.data["result"]["stdout"] == "Hello, World!"
        assert message.data["result"]["exit_code"] == 0
    
    @pytest.mark.asyncio
    async def test_send_ai_response(self, router, mock_manager):
        """Test AI response sending"""
        session_id = "test_session"
        chat_message = ChatMessage(
            id="msg_123",
            content="Boo! Your code looks spooky good! 👻",
            sender="ghost",
            timestamp=datetime.utcnow()
        )
        
        await router.send_ai_response(session_id, chat_message)
        
        assert len(mock_manager.sent_messages) == 1
        session, message = mock_manager.sent_messages[0]
        assert session == session_id
        assert message.type == WebSocketMessageType.AI_RESPONSE
        assert message.data["message"]["content"] == chat_message.content
        assert message.data["message"]["sender"] == "ghost"
    
    @pytest.mark.asyncio
    async def test_set_ai_typing(self, router, mock_manager):
        """Test AI typing indicator"""
        session_id = "test_session"
        
        # Set typing to true
        await router.set_ai_typing(session_id, True)
        
        assert len(mock_manager.sent_messages) == 1
        session, message = mock_manager.sent_messages[0]
        assert session == session_id
        assert message.type == WebSocketMessageType.AI_TYPING
        assert message.data["is_typing"] is True
        
        # Set typing to false
        await router.set_ai_typing(session_id, False)
        
        assert len(mock_manager.sent_messages) == 2
        session, message = mock_manager.sent_messages[1]
        assert message.data["is_typing"] is False
    
    @pytest.mark.asyncio
    async def test_notify_hook_triggered(self, router, mock_manager):
        """Test hook triggered notification"""
        session_id = "test_session"
        hook_type = "on_run"
        context = {"language": "python", "code_length": 100}
        
        await router.notify_hook_triggered(session_id, hook_type, context)
        
        assert len(mock_manager.sent_messages) == 1
        session, message = mock_manager.sent_messages[0]
        assert session == session_id
        assert message.type == WebSocketMessageType.HOOK_TRIGGERED
        assert message.data["hook_type"] == hook_type
        assert message.data["context"] == context
    
    @pytest.mark.asyncio
    async def test_notify_file_saved(self, router, mock_manager):
        """Test file saved notification"""
        session_id = "test_session"
        file_id = "file_123"
        file_name = "main.py"
        language = "python"
        
        await router.notify_file_saved(session_id, file_id, file_name, language)
        
        assert len(mock_manager.sent_messages) == 1
        session, message = mock_manager.sent_messages[0]
        assert session == session_id
        assert message.type == WebSocketMessageType.FILE_SAVED
        assert message.data["file_id"] == file_id
        assert message.data["file_name"] == file_name
        assert message.data["language"] == language


if __name__ == "__main__":
    pytest.main([__file__, "-v"])