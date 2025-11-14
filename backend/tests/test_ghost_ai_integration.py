"""
Integration tests for Ghost AI Service with API endpoints
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient

from app.main import app
from app.services.ghost_ai import HookEventType


class TestGhostAIIntegration:
    """Integration tests for Ghost AI API endpoints"""
    
    @pytest.mark.asyncio
    async def test_ghost_health_check(self):
        """Test Ghost AI health check endpoint"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client, \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello from the spectral realm!"
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/ghost/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "haunting"
                assert "👻" in data["message"]
                assert "test_response" in data
    
    @pytest.mark.asyncio
    async def test_ghost_health_check_failure(self):
        """Test Ghost AI health check when service fails"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client, \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            mock_client.return_value.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/ghost/health")
                
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "exorcised"
                assert "💀" in data["message"]
    
    @pytest.mark.asyncio
    async def test_chat_with_ghost(self):
        """Test chatting with Ghost AI"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client, \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Greetings, mortal! Your code awakens from the digital realm... 👻"
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                chat_request = {
                    "message": "Help me debug my Python code",
                    "session_id": "test-session-123",
                    "context": {
                        "chat_history": [],
                        "current_code": "print('hello world')",
                        "language": "python",
                        "recent_errors": [],
                        "session_id": "test-session-123",
                        "user_preferences": {}
                    }
                }
                
                response = await client.post("/api/v1/ghost/chat", json=chat_request)
                
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert "timestamp" in data
                assert "👻" in data["response"]
    
    @pytest.mark.asyncio
    async def test_hook_event_on_run(self):
        """Test on_run hook event handling"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client, \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Your code rises from the digital grave! 👻"
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                hook_request = {
                    "event": {
                        "event_type": "on_run",
                        "session_id": "test-session-123",
                        "data": {
                            "code": "print('Hello, Ghost!')",
                            "language": "python"
                        }
                    },
                    "context": {
                        "chat_history": [],
                        "current_code": "print('Hello, Ghost!')",
                        "language": "python",
                        "recent_errors": [],
                        "session_id": "test-session-123",
                        "user_preferences": {}
                    }
                }
                
                response = await client.post("/api/v1/ghost/hook-event", json=hook_request)
                
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert "👻" in data["response"]
    
    @pytest.mark.asyncio
    async def test_hook_event_on_error(self):
        """Test on_error hook event handling"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client, \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "A disturbance in the code... the spirits are restless! 👻"
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                hook_request = {
                    "event": {
                        "event_type": "on_error",
                        "session_id": "test-session-123",
                        "data": {
                            "error": "SyntaxError: invalid syntax at line 1",
                            "code": "print('Hello, Ghost!'"
                        }
                    },
                    "context": {
                        "chat_history": [],
                        "current_code": "print('Hello, Ghost!'",
                        "language": "python",
                        "recent_errors": ["SyntaxError: invalid syntax at line 1"],
                        "session_id": "test-session-123",
                        "user_preferences": {}
                    }
                }
                
                response = await client.post("/api/v1/ghost/hook-event", json=hook_request)
                
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert "👻" in data["response"]
    
    @pytest.mark.asyncio
    async def test_hook_event_on_save(self):
        """Test on_save hook event handling"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client, \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Your code has been preserved in the spectral archives... 👻"
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                hook_request = {
                    "event": {
                        "event_type": "on_save",
                        "session_id": "test-session-123",
                        "data": {
                            "code": "def hello_world():\n    print('Hello, Ghost!')\n    return 'success'"
                        }
                    },
                    "context": {
                        "chat_history": [],
                        "current_code": "def hello_world():\n    print('Hello, Ghost!')\n    return 'success'",
                        "language": "python",
                        "recent_errors": [],
                        "session_id": "test-session-123",
                        "user_preferences": {}
                    }
                }
                
                response = await client.post("/api/v1/ghost/hook-event", json=hook_request)
                
                assert response.status_code == 200
                data = response.json()
                assert "response" in data
                assert "👻" in data["response"]
    
    @pytest.mark.asyncio
    async def test_generate_code_snippet(self):
        """Test code snippet generation"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client, \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = """# Summoning a spectral greeting function
def ethereal_hello():
    phantom_message = "Hello from the other side!"
    print(phantom_message)
    return phantom_message"""
            mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                code_request = {
                    "description": "Create a hello world function",
                    "language": "python",
                    "context": "This is for a beginner tutorial",
                    "spooky_level": 3
                }
                
                response = await client.post("/api/v1/ghost/generate-code", json=code_request)
                
                assert response.status_code == 200
                data = response.json()
                assert "code" in data
                assert "language" in data
                assert "spooky_level" in data
                assert data["language"] == "python"
                assert data["spooky_level"] == 3
                assert "ethereal_hello" in data["code"]
    
    @pytest.mark.asyncio
    async def test_get_personality(self):
        """Test getting Ghost AI personality"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI'), \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/ghost/personality")
                
                assert response.status_code == 200
                data = response.json()
                assert "name" in data
                assert "traits" in data
                assert "vocabulary_style" in data
                assert "response_templates" in data
                assert data["name"] == "Spectral"
    
    @pytest.mark.asyncio
    async def test_update_personality(self):
        """Test updating Ghost AI personality"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI'), \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                new_personality = {
                    "name": "TestGhost",
                    "traits": ["helpful", "mysterious"],
                    "vocabulary_style": "test",
                    "response_templates": {
                        "encouragement": ["Great job!"],
                        "mockery": ["Could be better..."],
                        "debugging": ["Let me help..."],
                        "code_review": ["This looks good..."]
                    }
                }
                
                response = await client.put("/api/v1/ghost/personality", json=new_personality)
                
                assert response.status_code == 200
                data = response.json()
                assert "message" in data
                assert "personality" in data
                assert data["personality"]["name"] == "TestGhost"
    
    @pytest.mark.asyncio
    async def test_chat_error_handling(self):
        """Test error handling in chat endpoint"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client, \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = "test-api-key"
            mock_client.return_value.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                chat_request = {
                    "message": "Test message",
                    "session_id": "test-session",
                    "context": {
                        "chat_history": [],
                        "current_code": "",
                        "language": "python",
                        "recent_errors": [],
                        "session_id": "test-session",
                        "user_preferences": {}
                    }
                }
                
                response = await client.post("/api/v1/ghost/chat", json=chat_request)
                
                assert response.status_code == 500
                data = response.json()
                assert "👻" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_missing_openai_key(self):
        """Test behavior when OpenAI API key is missing"""
        with patch('app.core.config.settings') as mock_settings, \
             patch('app.api.endpoints.ghost_ai.GHOST_AI_SERVICE', None):
            
            mock_settings.openai_api_key = None
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/api/v1/ghost/health")
                
                assert response.status_code == 500
                data = response.json()
                assert "incantations" in data["detail"]
                assert "👻" in data["detail"]