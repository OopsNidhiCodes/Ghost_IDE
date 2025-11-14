"""
End-to-End Integration Tests for GhostIDE Backend
Tests complete workflows including code execution, AI interaction, and session management
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from unittest.mock import AsyncMock, patch, MagicMock

from app.main import app
from app.services.session_manager import SessionManager
from app.services.code_execution import CodeExecutionService
from app.services.ghost_ai import GhostAIService
from app.services.hook_manager import HookManagerService
from app.models.schemas import CodeFile, UserSession, ExecutionRequest


class TestEndToEndIntegration:
    """Test complete end-to-end workflows"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager"""
        with patch('app.services.session_manager.session_manager') as mock:
            mock.create_session = AsyncMock(return_value="test-session-123")
            mock.get_session = AsyncMock(return_value={
                "id": "test-session-123",
                "files": [],
                "chat_history": [],
                "preferences": {"theme": "ghost-dark"},
                "current_language": "python",
                "last_activity": "2023-01-01T00:00:00Z"
            })
            mock.update_session = AsyncMock()
            mock.add_file = AsyncMock()
            mock.update_file = AsyncMock()
            yield mock

    @pytest.fixture
    def mock_code_execution(self):
        """Mock code execution service"""
        with patch('app.services.code_execution.CodeExecutionService') as mock_class:
            mock_instance = AsyncMock()
            mock_instance.execute_code = AsyncMock(return_value={
                "stdout": "Hello, World!\n",
                "stderr": "",
                "exit_code": 0,
                "execution_time": 0.123
            })
            mock_instance.validate_code = AsyncMock(return_value=True)
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_ghost_ai(self):
        """Mock Ghost AI service"""
        with patch('app.services.ghost_ai.GhostAIService') as mock_class:
            mock_instance = AsyncMock()
            mock_instance.generate_response = AsyncMock(
                return_value="Ah, mortal! Your code pleases the spirits... 👻"
            )
            mock_instance.react_to_event = AsyncMock(
                return_value="The ethereal realm trembles with your code execution!"
            )
            mock_class.return_value = mock_instance
            yield mock_instance

    @pytest.fixture
    def mock_hook_manager(self):
        """Mock hook manager"""
        with patch('app.services.hook_manager.hook_manager') as mock:
            mock.trigger_hook = AsyncMock()
            yield mock

    def test_complete_code_execution_workflow(
        self, 
        client, 
        mock_session_manager, 
        mock_code_execution, 
        mock_ghost_ai, 
        mock_hook_manager
    ):
        """Test complete code execution workflow from API to hooks"""
        
        # 1. Create session
        response = client.post("/api/v1/sessions", json={
            "preferences": {"theme": "ghost-dark"},
            "language": "python"
        })
        assert response.status_code == 200
        session_data = response.json()
        session_id = session_data["sessionId"]

        # 2. Add a file
        file_data = {
            "name": "test.py",
            "content": 'print("Hello, World!")',
            "language": "python"
        }
        response = client.post(f"/api/v1/sessions/{session_id}/files", json=file_data)
        assert response.status_code == 200

        # 3. Execute code
        execution_data = {
            "code": 'print("Hello, World!")',
            "language": "python",
            "session_id": session_id
        }
        response = client.post("/api/v1/execution/execute", json=execution_data)
        assert response.status_code == 200
        
        result = response.json()
        assert result["stdout"] == "Hello, World!\n"
        assert result["exit_code"] == 0

        # Verify hooks were triggered
        mock_hook_manager.trigger_hook.assert_called()

    def test_language_switching_workflow(
        self, 
        client, 
        mock_session_manager, 
        mock_ghost_ai
    ):
        """Test seamless language switching with session preservation"""
        
        # 1. Create session with Python
        response = client.post("/api/v1/sessions", json={
            "preferences": {"theme": "ghost-dark"},
            "language": "python"
        })
        assert response.status_code == 200
        session_id = response.json()["sessionId"]

        # 2. Add Python file
        response = client.post(f"/api/v1/sessions/{session_id}/files", json={
            "name": "test.py",
            "content": 'print("Hello from Python!")',
            "language": "python"
        })
        assert response.status_code == 200
        file_id = response.json()["id"]

        # 3. Switch to JavaScript
        response = client.put(f"/api/v1/sessions/{session_id}", json={
            "current_language": "javascript"
        })
        assert response.status_code == 200

        # 4. Update file for new language
        response = client.put(f"/api/v1/sessions/{session_id}/files/{file_id}", json={
            "name": "test.js",
            "content": 'console.log("Hello from JavaScript!");',
            "language": "javascript"
        })
        assert response.status_code == 200

        # 5. Get language configuration
        response = client.get("/api/v1/languages/javascript")
        assert response.status_code == 200
        config = response.json()
        assert config["name"] == "JavaScript"

    def test_ghost_ai_interaction_workflow(
        self, 
        client, 
        mock_session_manager, 
        mock_ghost_ai
    ):
        """Test Ghost AI interaction with context awareness"""
        
        # 1. Create session
        response = client.post("/api/v1/sessions", json={
            "preferences": {"theme": "ghost-dark"},
            "language": "python"
        })
        session_id = response.json()["sessionId"]

        # 2. Send chat message
        chat_data = {
            "message": "Help me debug this code",
            "context": {
                "current_code": 'print("Hello"',  # Intentional syntax error
                "language": "python",
                "recent_output": {"stderr": "SyntaxError: unexpected EOF"}
            }
        }
        response = client.post(f"/api/v1/ghost/chat/{session_id}", json=chat_data)
        assert response.status_code == 200
        
        ai_response = response.json()
        assert "message" in ai_response
        
        # Verify AI was called with context
        mock_ghost_ai.generate_response.assert_called()

    def test_session_persistence_workflow(
        self, 
        client, 
        mock_session_manager
    ):
        """Test session creation, updates, and restoration"""
        
        # 1. Create session
        response = client.post("/api/v1/sessions", json={
            "preferences": {"theme": "ghost-dark", "fontSize": 14},
            "language": "python"
        })
        assert response.status_code == 200
        session_id = response.json()["sessionId"]

        # 2. Add multiple files
        files_data = [
            {"name": "main.py", "content": "print('main')", "language": "python"},
            {"name": "utils.py", "content": "def helper(): pass", "language": "python"}
        ]
        
        for file_data in files_data:
            response = client.post(f"/api/v1/sessions/{session_id}/files", json=file_data)
            assert response.status_code == 200

        # 3. Update session preferences
        response = client.put(f"/api/v1/sessions/{session_id}", json={
            "preferences": {"theme": "ghost-light", "fontSize": 16}
        })
        assert response.status_code == 200

        # 4. Sync session data
        sync_data = {
            "files": [
                {"id": "file1", "name": "main.py", "content": "print('updated')", "lastModified": "2023-01-01T00:00:00Z"}
            ],
            "chatHistory": [
                {"id": "msg1", "content": "Hello", "sender": "user", "timestamp": "2023-01-01T00:00:00Z"}
            ],
            "preferences": {"theme": "ghost-dark"},
            "lastActivity": "2023-01-01T00:00:00Z"
        }
        response = client.put(f"/api/v1/sessions/{session_id}/sync", json=sync_data)
        assert response.status_code == 200

        # 5. Retrieve session
        response = client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 200
        
        session_data = response.json()
        assert session_data["id"] == session_id

    def test_hook_system_integration(
        self, 
        client, 
        mock_session_manager, 
        mock_code_execution, 
        mock_ghost_ai, 
        mock_hook_manager
    ):
        """Test hook system integration with code events"""
        
        # 1. Create session
        response = client.post("/api/v1/sessions")
        session_id = response.json()["sessionId"]

        # 2. Trigger on_run hook
        hook_data = {
            "type": "on_run",
            "data": {
                "code": 'print("Hello")',
                "language": "python",
                "timestamp": "2023-01-01T00:00:00Z"
            },
            "session_id": session_id
        }
        response = client.post("/api/v1/hooks/trigger", json=hook_data)
        assert response.status_code == 200

        # 3. Trigger on_error hook
        hook_data["type"] = "on_error"
        hook_data["data"]["error"] = "SyntaxError: invalid syntax"
        response = client.post("/api/v1/hooks/trigger", json=hook_data)
        assert response.status_code == 200

        # 4. Trigger on_save hook
        hook_data["type"] = "on_save"
        hook_data["data"] = {
            "file": {"name": "test.py", "content": "print('saved')"},
            "timestamp": "2023-01-01T00:00:00Z"
        }
        response = client.post("/api/v1/hooks/trigger", json=hook_data)
        assert response.status_code == 200

        # Verify all hooks were triggered
        assert mock_hook_manager.trigger_hook.call_count == 3

    def test_security_and_validation_workflow(
        self, 
        client, 
        mock_code_execution
    ):
        """Test security measures and input validation"""
        
        # 1. Test rate limiting (would need actual rate limiting implementation)
        session_response = client.post("/api/v1/sessions")
        session_id = session_response.json()["sessionId"]

        # 2. Test code validation
        malicious_code = {
            "code": "import os; os.system('rm -rf /')",  # Malicious code
            "language": "python",
            "session_id": session_id
        }
        
        # Should be handled by validation
        mock_code_execution.validate_code.return_value = False
        response = client.post("/api/v1/execution/execute", json=malicious_code)
        # Response depends on validation implementation
        
        # 3. Test input sanitization
        invalid_session_data = {
            "preferences": {"theme": "<script>alert('xss')</script>"},
            "language": "python"
        }
        response = client.post("/api/v1/sessions", json=invalid_session_data)
        # Should sanitize or reject malicious input

    def test_error_handling_and_recovery(
        self, 
        client, 
        mock_session_manager, 
        mock_code_execution
    ):
        """Test error handling and graceful recovery"""
        
        # 1. Test session creation failure
        mock_session_manager.create_session.side_effect = Exception("Database error")
        response = client.post("/api/v1/sessions")
        assert response.status_code == 500

        # Reset mock
        mock_session_manager.create_session.side_effect = None
        mock_session_manager.create_session.return_value = "test-session"

        # 2. Test code execution failure
        mock_code_execution.execute_code.side_effect = Exception("Execution failed")
        
        response = client.post("/api/v1/sessions")
        session_id = response.json()["sessionId"]
        
        execution_data = {
            "code": 'print("test")',
            "language": "python",
            "session_id": session_id
        }
        response = client.post("/api/v1/execution/execute", json=execution_data)
        assert response.status_code == 500

    def test_performance_and_caching(
        self, 
        client, 
        mock_session_manager
    ):
        """Test performance optimizations and caching"""
        
        # 1. Test language configuration caching
        # First request
        response1 = client.get("/api/v1/languages/python")
        assert response1.status_code == 200
        
        # Second request (should use cache)
        response2 = client.get("/api/v1/languages/python")
        assert response2.status_code == 200
        assert response1.json() == response2.json()

        # 2. Test session data caching
        response = client.post("/api/v1/sessions")
        session_id = response.json()["sessionId"]
        
        # Multiple requests for same session
        for _ in range(3):
            response = client.get(f"/api/v1/sessions/{session_id}")
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_websocket_integration_workflow(self, mock_ghost_ai, mock_code_execution):
        """Test WebSocket integration for real-time communication"""
        
        with TestClient(app) as client:
            # Test WebSocket connection
            with client.websocket_connect("/ws/test-session") as websocket:
                # 1. Test code execution via WebSocket
                execution_message = {
                    "type": "execute_code",
                    "data": {
                        "code": 'print("Hello via WebSocket")',
                        "language": "python",
                        "session_id": "test-session"
                    }
                }
                websocket.send_json(execution_message)
                
                # Should receive execution start message
                response = websocket.receive_json()
                assert response["type"] == "execution_start"
                
                # Should receive execution complete message
                response = websocket.receive_json()
                assert response["type"] == "execution_complete"

                # 2. Test Ghost AI chat via WebSocket
                chat_message = {
                    "type": "ghost_chat",
                    "data": {
                        "message": "Hello Ghost!",
                        "session_id": "test-session",
                        "context": {"language": "python"}
                    }
                }
                websocket.send_json(chat_message)
                
                # Should receive ghost response
                response = websocket.receive_json()
                assert response["type"] == "ghost_response"
                assert "message" in response["data"]

    def test_complete_user_scenario(
        self, 
        client, 
        mock_session_manager, 
        mock_code_execution, 
        mock_ghost_ai, 
        mock_hook_manager
    ):
        """Test complete user scenario from start to finish"""
        
        # 1. User creates new session
        response = client.post("/api/v1/sessions", json={
            "preferences": {"theme": "ghost-dark", "fontSize": 14},
            "language": "python"
        })
        assert response.status_code == 200
        session_id = response.json()["sessionId"]

        # 2. User creates a file
        response = client.post(f"/api/v1/sessions/{session_id}/files", json={
            "name": "hello.py",
            "content": 'print("Hello, Ghost IDE!")',
            "language": "python"
        })
        assert response.status_code == 200
        file_id = response.json()["id"]

        # 3. User executes code
        response = client.post("/api/v1/execution/execute", json={
            "code": 'print("Hello, Ghost IDE!")',
            "language": "python",
            "session_id": session_id
        })
        assert response.status_code == 200
        assert "Hello, Ghost IDE!" in response.json()["stdout"]

        # 4. User chats with Ghost AI
        response = client.post(f"/api/v1/ghost/chat/{session_id}", json={
            "message": "Great! The code works perfectly!",
            "context": {
                "current_code": 'print("Hello, Ghost IDE!")',
                "language": "python",
                "recent_output": {"stdout": "Hello, Ghost IDE!\n"}
            }
        })
        assert response.status_code == 200

        # 5. User switches language
        response = client.put(f"/api/v1/sessions/{session_id}", json={
            "current_language": "javascript"
        })
        assert response.status_code == 200

        # 6. User updates file for new language
        response = client.put(f"/api/v1/sessions/{session_id}/files/{file_id}", json={
            "name": "hello.js",
            "content": 'console.log("Hello, Ghost IDE!");',
            "language": "javascript"
        })
        assert response.status_code == 200

        # 7. User executes JavaScript code
        mock_code_execution.execute_code.return_value = {
            "stdout": "Hello, Ghost IDE!\n",
            "stderr": "",
            "exit_code": 0,
            "execution_time": 0.089
        }
        
        response = client.post("/api/v1/execution/execute", json={
            "code": 'console.log("Hello, Ghost IDE!");',
            "language": "javascript",
            "session_id": session_id
        })
        assert response.status_code == 200

        # 8. Verify session state
        response = client.get(f"/api/v1/sessions/{session_id}")
        assert response.status_code == 200
        session_data = response.json()
        assert session_data["current_language"] == "javascript"

        # Verify hooks were triggered throughout the workflow
        assert mock_hook_manager.trigger_hook.call_count >= 2  # At least on_run hooks