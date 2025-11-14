"""
Unit tests for Pydantic models and database models
"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.models.schemas import (
    UserPreferences, CodeFile, CodeFileCreate, UserSession, 
    ExecutionRequest, LanguageType
)


class TestUserPreferences:
    """Test UserPreferences model"""
    
    def test_default_values(self):
        """Test default values are set correctly"""
        prefs = UserPreferences()
        assert prefs.theme == "ghost-dark"
        assert prefs.font_size == 14
        assert prefs.auto_save is True
        assert prefs.auto_save_interval == 30
    
    def test_valid_font_size_range(self):
        """Test font size validation"""
        # Valid sizes
        prefs = UserPreferences(font_size=8)
        assert prefs.font_size == 8
        
        prefs = UserPreferences(font_size=32)
        assert prefs.font_size == 32
        
        # Invalid sizes
        with pytest.raises(ValidationError):
            UserPreferences(font_size=7)
        
        with pytest.raises(ValidationError):
            UserPreferences(font_size=33)
    
    def test_valid_auto_save_interval(self):
        """Test auto save interval validation"""
        # Valid intervals
        prefs = UserPreferences(auto_save_interval=5)
        assert prefs.auto_save_interval == 5
        
        prefs = UserPreferences(auto_save_interval=300)
        assert prefs.auto_save_interval == 300
        
        # Invalid intervals
        with pytest.raises(ValidationError):
            UserPreferences(auto_save_interval=4)
        
        with pytest.raises(ValidationError):
            UserPreferences(auto_save_interval=301)


class TestCodeFile:
    """Test CodeFile models"""
    
    def test_code_file_create_valid(self):
        """Test valid CodeFileCreate"""
        file_data = CodeFileCreate(
            name="test.py",
            content="print('Hello Ghost!')",
            language=LanguageType.PYTHON
        )
        assert file_data.name == "test.py"
        assert file_data.content == "print('Hello Ghost!')"
        assert file_data.language == LanguageType.PYTHON
    
    def test_code_file_name_validation(self):
        """Test file name validation"""
        # Valid name
        CodeFileCreate(name="test.py", language=LanguageType.PYTHON)
        
        # Invalid names
        with pytest.raises(ValidationError):
            CodeFileCreate(name="", language=LanguageType.PYTHON)
        
        with pytest.raises(ValidationError):
            CodeFileCreate(name="a" * 256, language=LanguageType.PYTHON)
    
    def test_code_file_complete(self):
        """Test complete CodeFile model"""
        now = datetime.utcnow()
        file_data = CodeFile(
            id="test-id",
            name="test.py",
            content="print('Boo!')",
            language=LanguageType.PYTHON,
            last_modified=now
        )
        assert file_data.id == "test-id"
        assert file_data.last_modified == now


class TestExecutionRequest:
    """Test ExecutionRequest model"""
    
    def test_valid_execution_request(self):
        """Test valid execution request"""
        request = ExecutionRequest(
            code="print('Hello')",
            language=LanguageType.PYTHON,
            session_id="test-session"
        )
        assert request.code == "print('Hello')"
        assert request.language == LanguageType.PYTHON
        assert request.timeout == 30  # default
        assert request.session_id == "test-session"
    
    def test_execution_request_with_input(self):
        """Test execution request with input"""
        request = ExecutionRequest(
            code="name = input('Name: ')",
            language=LanguageType.PYTHON,
            input="Ghost",
            timeout=60,
            session_id="test-session"
        )
        assert request.input == "Ghost"
        assert request.timeout == 60
    
    def test_timeout_validation(self):
        """Test timeout validation"""
        # Valid timeouts
        ExecutionRequest(
            code="print('test')",
            language=LanguageType.PYTHON,
            timeout=1,
            session_id="test"
        )
        
        ExecutionRequest(
            code="print('test')",
            language=LanguageType.PYTHON,
            timeout=300,
            session_id="test"
        )
        
        # Invalid timeouts
        with pytest.raises(ValidationError):
            ExecutionRequest(
                code="print('test')",
                language=LanguageType.PYTHON,
                timeout=0,
                session_id="test"
            )
        
        with pytest.raises(ValidationError):
            ExecutionRequest(
                code="print('test')",
                language=LanguageType.PYTHON,
                timeout=301,
                session_id="test"
            )
    
    def test_empty_code_validation(self):
        """Test empty code validation"""
        with pytest.raises(ValidationError):
            ExecutionRequest(
                code="",
                language=LanguageType.PYTHON,
                session_id="test"
            )


class TestUserSession:
    """Test UserSession model"""
    
    def test_user_session_defaults(self):
        """Test UserSession default values"""
        now = datetime.utcnow()
        session = UserSession(
            id="test-id",
            created_at=now,
            last_activity=now
        )
        assert session.current_language == LanguageType.PYTHON
        assert session.preferences.theme == "ghost-dark"
        assert session.files == []
        assert session.chat_history == []
    
    def test_user_session_with_data(self):
        """Test UserSession with files and chat history"""
        from app.models.schemas import ChatMessage
        
        now = datetime.utcnow()
        
        code_file = CodeFile(
            id="file-1",
            name="main.py",
            content="print('Spooky!')",
            language=LanguageType.PYTHON,
            last_modified=now
        )
        
        chat_message = ChatMessage(
            id="msg-1",
            content="Hello ghost!",
            sender="user",
            timestamp=now
        )
        
        session = UserSession(
            id="session-1",
            files=[code_file],
            chat_history=[chat_message],
            created_at=now,
            last_activity=now
        )
        
        assert len(session.files) == 1
        assert session.files[0].name == "main.py"
        assert len(session.chat_history) == 1
        assert session.chat_history[0].content == "Hello ghost!"


class TestLanguageType:
    """Test LanguageType enum"""
    
    def test_supported_languages(self):
        """Test all supported languages"""
        assert LanguageType.PYTHON == "python"
        assert LanguageType.JAVASCRIPT == "javascript"
        assert LanguageType.JAVA == "java"
        assert LanguageType.CPP == "cpp"
        assert LanguageType.C == "c"
    
    def test_language_validation_in_models(self):
        """Test language validation in models"""
        # Valid language
        CodeFileCreate(name="test.py", language=LanguageType.PYTHON)
        
        # Test that string values work
        file_data = CodeFileCreate(name="test.js", language="javascript")
        assert file_data.language == LanguageType.JAVASCRIPT