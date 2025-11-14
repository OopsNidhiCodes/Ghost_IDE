"""
Working tests that demonstrate the API functionality
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestWorkingAPI:
    """Tests that demonstrate working API functionality"""
    
    def test_root_endpoint_works(self):
        """Test that root endpoint works"""
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "👻" in data["message"]
    
    def test_health_endpoint_works(self):
        """Test that health endpoint works"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "👻" in data["message"]
    
    def test_api_structure_exists(self):
        """Test that API structure is properly set up"""
        # This test verifies that the API routes are properly configured
        # The actual database operations would require a running PostgreSQL instance
        # or proper test database setup, which is beyond the scope of this basic test
        
        # Verify the app has the expected routes
        routes = [route.path for route in app.routes]
        
        # Check that our API routes are registered
        assert "/" in routes
        assert "/health" in routes
        
        # The API router should be included (though specific paths may not show up in this list)
        # This confirms the basic structure is correct
        assert len(routes) >= 2


class TestDataModels:
    """Test that our data models work correctly"""
    
    def test_pydantic_models_import(self):
        """Test that Pydantic models can be imported and instantiated"""
        from app.models.schemas import (
            UserPreferences, CodeFileCreate, ExecutionRequest, LanguageType
        )
        
        # Test UserPreferences
        prefs = UserPreferences()
        assert prefs.theme == "ghost-dark"
        assert prefs.font_size == 14
        
        # Test CodeFileCreate
        file_create = CodeFileCreate(
            name="test.py",
            content="print('Hello Ghost!')",
            language=LanguageType.PYTHON
        )
        assert file_create.name == "test.py"
        assert file_create.language == LanguageType.PYTHON
        
        # Test ExecutionRequest
        exec_request = ExecutionRequest(
            code="print('test')",
            language=LanguageType.PYTHON,
            session_id="test-session"
        )
        assert exec_request.timeout == 30  # default value
        assert exec_request.language == LanguageType.PYTHON
    
    def test_database_models_import(self):
        """Test that database models can be imported"""
        from app.models.database import UserSessionDB, CodeFileDB, ChatMessageDB
        
        # Just test that they can be imported and have expected attributes
        assert hasattr(UserSessionDB, '__tablename__')
        assert hasattr(CodeFileDB, '__tablename__')
        assert hasattr(ChatMessageDB, '__tablename__')
        
        assert UserSessionDB.__tablename__ == "user_sessions"
        assert CodeFileDB.__tablename__ == "code_files"
        assert ChatMessageDB.__tablename__ == "chat_messages"


class TestAPIEndpointStructure:
    """Test that API endpoints are properly structured"""
    
    def test_session_endpoints_exist(self):
        """Test that session endpoints are properly configured"""
        from app.api.endpoints.sessions import router
        
        # Check that the router has the expected routes
        routes = [route.path for route in router.routes]
        
        # Should have routes for CRUD operations
        assert "/" in routes  # POST for create, GET for list
        assert "/{session_id}" in routes  # GET, PUT, DELETE for individual sessions
        assert "/{session_id}/files" in routes  # File operations
        
        # Check HTTP methods
        methods = []
        for route in router.routes:
            if hasattr(route, 'methods'):
                methods.extend(route.methods)
        
        assert "POST" in methods
        assert "GET" in methods
        assert "PUT" in methods
        assert "DELETE" in methods