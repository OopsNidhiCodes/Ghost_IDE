"""
Unit tests for Ghost AI Service
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.ghost_ai import (
    GhostAIService, 
    GhostPersonality, 
    AIContext, 
    CodeGenerationRequest,
    HookEvent,
    HookEventType
)
from app.models.schemas import LanguageType


class TestGhostPersonality:
    """Test Ghost AI personality configuration"""
    
    def test_default_personality(self):
        """Test default personality configuration"""
        personality = GhostPersonality()
        
        assert personality.name == "Spectral"
        assert "darkly humorous" in personality.traits
        assert "sarcastic" in personality.traits
        assert personality.vocabulary_style == "spooky"
        assert "encouragement" in personality.response_templates
        assert "mockery" in personality.response_templates
        assert "debugging" in personality.response_templates
        assert "code_review" in personality.response_templates
    
    def test_custom_personality(self):
        """Test custom personality configuration"""
        custom_traits = ["mysterious", "helpful"]
        custom_templates = {
            "encouragement": ["Great job, mortal!"],
            "mockery": ["Even a zombie could do better..."]
        }
        
        personality = GhostPersonality(
            name="TestGhost",
            traits=custom_traits,
            vocabulary_style="test",
            response_templates=custom_templates
        )
        
        assert personality.name == "TestGhost"
        assert personality.traits == custom_traits
        assert personality.vocabulary_style == "test"
        assert personality.response_templates == custom_templates


class TestAIContext:
    """Test AI context model"""
    
    def test_default_context(self):
        """Test default AI context"""
        context = AIContext()
        
        assert context.chat_history == []
        assert context.current_code == ""
        assert context.language == LanguageType.PYTHON
        assert context.recent_errors == []
        assert context.session_id == ""
        assert context.user_preferences == {}
    
    def test_context_with_data(self):
        """Test AI context with data"""
        chat_history = [{"sender": "user", "content": "Hello"}]
        code = "print('hello world')"
        errors = ["SyntaxError: invalid syntax"]
        
        context = AIContext(
            chat_history=chat_history,
            current_code=code,
            language=LanguageType.JAVASCRIPT,
            recent_errors=errors,
            session_id="test-session",
            user_preferences={"theme": "dark"}
        )
        
        assert context.chat_history == chat_history
        assert context.current_code == code
        assert context.language == LanguageType.JAVASCRIPT
        assert context.recent_errors == errors
        assert context.session_id == "test-session"
        assert context.user_preferences == {"theme": "dark"}


class TestCodeGenerationRequest:
    """Test code generation request model"""
    
    def test_valid_request(self):
        """Test valid code generation request"""
        request = CodeGenerationRequest(
            description="Create a hello world function",
            language=LanguageType.PYTHON,
            context="This is for a beginner tutorial",
            spooky_level=3
        )
        
        assert request.description == "Create a hello world function"
        assert request.language == LanguageType.PYTHON
        assert request.context == "This is for a beginner tutorial"
        assert request.spooky_level == 3
    
    def test_spooky_level_validation(self):
        """Test spooky level validation"""
        # Valid spooky levels
        for level in [1, 2, 3, 4, 5]:
            request = CodeGenerationRequest(
                description="test",
                language=LanguageType.PYTHON,
                spooky_level=level
            )
            assert request.spooky_level == level
        
        # Invalid spooky levels should raise validation error
        with pytest.raises(ValueError):
            CodeGenerationRequest(
                description="test",
                language=LanguageType.PYTHON,
                spooky_level=0
            )
        
        with pytest.raises(ValueError):
            CodeGenerationRequest(
                description="test",
                language=LanguageType.PYTHON,
                spooky_level=6
            )


class TestHookEvent:
    """Test hook event model"""
    
    def test_hook_event_creation(self):
        """Test hook event creation"""
        event_data = {"code": "print('test')", "language": "python"}
        event = HookEvent(
            event_type=HookEventType.ON_RUN,
            session_id="test-session",
            data=event_data
        )
        
        assert event.event_type == HookEventType.ON_RUN
        assert event.session_id == "test-session"
        assert event.data == event_data
        assert isinstance(event.timestamp, datetime)


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    with patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client:
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Spooky AI response! 👻"
        
        mock_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        yield mock_client


class TestGhostAIService:
    """Test Ghost AI Service functionality"""
    
    def test_service_initialization(self):
        """Test Ghost AI service initialization"""
        service = GhostAIService(api_key="test-key")
        
        assert service.personality.name == "Spectral"
        assert "You are Spectral" in service.system_prompt
        assert "supernatural entity" in service.system_prompt
    
    def test_custom_personality_initialization(self):
        """Test service initialization with custom personality"""
        custom_personality = GhostPersonality(name="TestGhost", traits=["helpful"])
        service = GhostAIService(api_key="test-key", personality=custom_personality)
        
        assert service.personality.name == "TestGhost"
        assert "You are TestGhost" in service.system_prompt
    
    @pytest.mark.asyncio
    async def test_generate_response(self, mock_openai_client):
        """Test basic response generation"""
        service = GhostAIService(api_key="test-key")
        context = AIContext()
        
        response = await service.generate_response("Hello ghost!", context)
        
        assert response == "Spooky AI response! 👻"
        mock_openai_client.return_value.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_with_context(self, mock_openai_client):
        """Test response generation with context"""
        service = GhostAIService(api_key="test-key")
        context = AIContext(
            chat_history=[{"sender": "user", "content": "Previous message"}],
            current_code="print('hello')",
            language=LanguageType.PYTHON
        )
        
        response = await service.generate_response("Help me debug this", context)
        
        assert response == "Spooky AI response! 👻"
        
        # Verify the call was made with proper context
        call_args = mock_openai_client.return_value.chat.completions.create.call_args
        messages = call_args[1]['messages']
        
        # Should have system prompt, context info, and user message
        assert len(messages) >= 3
        assert messages[0]['role'] == 'system'
        assert any('Current code' in msg['content'] for msg in messages if msg['role'] == 'system')
    
    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self):
        """Test error handling in response generation"""
        with patch('app.services.ghost_ai.openai.AsyncOpenAI') as mock_client:
            mock_client.return_value.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            
            service = GhostAIService(api_key="test-key")
            context = AIContext()
            
            response = await service.generate_response("Test prompt", context)
            
            # Should return fallback response
            assert "ethereal connection is disrupted" in response
    
    @pytest.mark.asyncio
    async def test_react_to_on_run_event(self, mock_openai_client):
        """Test reaction to on_run hook event"""
        service = GhostAIService(api_key="test-key")
        context = AIContext()
        
        event = HookEvent(
            event_type=HookEventType.ON_RUN,
            session_id="test-session",
            data={"code": "print('hello')", "language": "python"}
        )
        
        response = await service.react_to_event(event, context)
        
        assert response == "Spooky AI response! 👻"
        
        # Verify the prompt mentions code execution
        call_args = mock_openai_client.return_value.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = next(msg for msg in messages if msg['role'] == 'user')
        assert "executed" in user_message['content']
    
    @pytest.mark.asyncio
    async def test_react_to_on_error_event(self, mock_openai_client):
        """Test reaction to on_error hook event"""
        service = GhostAIService(api_key="test-key")
        context = AIContext()
        
        event = HookEvent(
            event_type=HookEventType.ON_ERROR,
            session_id="test-session",
            data={"error": "SyntaxError: invalid syntax", "code": "print('hello'"}
        )
        
        response = await service.react_to_event(event, context)
        
        assert response == "Spooky AI response! 👻"
        
        # Verify the prompt mentions the error
        call_args = mock_openai_client.return_value.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = next(msg for msg in messages if msg['role'] == 'user')
        assert "SyntaxError" in user_message['content']
    
    @pytest.mark.asyncio
    async def test_react_to_on_save_event(self, mock_openai_client):
        """Test reaction to on_save hook event"""
        service = GhostAIService(api_key="test-key")
        context = AIContext()
        
        event = HookEvent(
            event_type=HookEventType.ON_SAVE,
            session_id="test-session",
            data={"code": "def hello():\n    print('world')"}
        )
        
        response = await service.react_to_event(event, context)
        
        assert response == "Spooky AI response! 👻"
        
        # Verify the prompt mentions saving
        call_args = mock_openai_client.return_value.chat.completions.create.call_args
        messages = call_args[1]['messages']
        user_message = next(msg for msg in messages if msg['role'] == 'user')
        assert "saved" in user_message['content']
    
    @pytest.mark.asyncio
    async def test_generate_code_snippet(self, mock_openai_client):
        """Test code snippet generation"""
        # Mock response with actual code
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """# Summoning a spectral greeting function
def ethereal_hello():
    phantom_message = "Hello from the other side!"
    print(phantom_message)
    return phantom_message"""
        
        mock_openai_client.return_value.chat.completions.create = AsyncMock(return_value=mock_response)
        
        service = GhostAIService(api_key="test-key")
        request = CodeGenerationRequest(
            description="Create a hello world function",
            language=LanguageType.PYTHON,
            spooky_level=3
        )
        
        code = await service.generate_code_snippet(request)
        
        assert "ethereal_hello" in code
        assert "phantom_message" in code
        assert "def " in code
    
    def test_get_spooky_variables(self):
        """Test spooky variable name generation"""
        service = GhostAIService(api_key="test-key")
        
        # Test different spooky levels
        level_1_vars = service._get_spooky_variables(1)
        level_3_vars = service._get_spooky_variables(3)
        level_5_vars = service._get_spooky_variables(5)
        
        # Higher levels should have more variables
        assert len(level_1_vars) < len(level_3_vars) < len(level_5_vars)
        
        # Should contain base variables
        assert "result" in level_1_vars
        assert "data" in level_1_vars
        
        # Should contain spooky variables at appropriate levels
        assert "shadow_result" in level_1_vars
        assert "cursed_result" in level_3_vars
        assert "apocalyptic_result" in level_5_vars
    
    def test_get_personality_info(self):
        """Test personality info retrieval"""
        service = GhostAIService(api_key="test-key")
        info = service.get_personality_info()
        
        assert info["name"] == "Spectral"
        assert "traits" in info
        assert "vocabulary_style" in info
        assert "response_templates" in info
    
    def test_update_personality(self):
        """Test personality update"""
        service = GhostAIService(api_key="test-key")
        
        new_personality = GhostPersonality(name="NewGhost", traits=["friendly"])
        service.update_personality(new_personality)
        
        assert service.personality.name == "NewGhost"
        assert service.personality.traits == ["friendly"]
        assert "You are NewGhost" in service.system_prompt
    
    def test_fallback_responses(self):
        """Test fallback response generation"""
        service = GhostAIService(api_key="test-key")
        
        error_response = service._get_fallback_response("error")
        assert "ethereal connection is disrupted" in error_response
        
        run_response = service._get_fallback_response("on_run")
        assert "digital slumber" in run_response
        
        default_response = service._get_fallback_response("unknown")
        assert "temporarily unavailable" in default_response