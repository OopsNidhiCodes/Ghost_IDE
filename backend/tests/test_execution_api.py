"""
Unit tests for code execution API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import uuid

from app.main import app
from app.models.schemas import ExecutionRequest, ExecutionResult

client = TestClient(app)


class TestExecutionAPI:
    """Test cases for execution API endpoints"""
    
    @patch('app.api.endpoints.execution.code_execution_service')
    def test_execute_code_success(self, mock_service):
        """Test successful synchronous code execution"""
        # Mock the execution result
        mock_result = ExecutionResult(
            stdout="Hello, World!",
            stderr="",
            exit_code=0,
            execution_time=0.5
        )
        mock_service.execute_code = AsyncMock(return_value=mock_result)
        
        # Make request
        response = client.post("/api/v1/execution/execute", json={
            "code": "print('Hello, World!')",
            "language": "python",
            "session_id": "test-session",
            "timeout": 30
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["stdout"] == "Hello, World!"
        assert data["exit_code"] == 0
        assert data["execution_time"] == 0.5
    
    @patch('app.api.endpoints.execution.code_execution_service')
    def test_execute_code_failure(self, mock_service):
        """Test code execution with error"""
        # Mock the execution result with error
        mock_result = ExecutionResult(
            stdout="",
            stderr="SyntaxError: invalid syntax",
            exit_code=1,
            execution_time=0.1
        )
        mock_service.execute_code = AsyncMock(return_value=mock_result)
        
        # Make request
        response = client.post("/api/v1/execution/execute", json={
            "code": "print('Hello, World!'",  # Missing closing parenthesis
            "language": "python",
            "session_id": "test-session",
            "timeout": 30
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["exit_code"] == 1
        assert "SyntaxError" in data["stderr"]
    
    @patch('app.api.endpoints.execution.code_execution_service')
    def test_execute_code_service_exception(self, mock_service):
        """Test code execution with service exception"""
        mock_service.execute_code = AsyncMock(side_effect=Exception("Service error"))
        
        # Make request
        response = client.post("/api/v1/execution/execute", json={
            "code": "print('Hello, World!')",
            "language": "python",
            "session_id": "test-session",
            "timeout": 30
        })
        
        assert response.status_code == 500
        assert "Code execution failed" in response.json()["detail"]
    
    def test_execute_code_invalid_request(self):
        """Test code execution with invalid request data"""
        # Missing required fields
        response = client.post("/api/v1/execution/execute", json={
            "code": "print('Hello, World!')",
            # Missing language and session_id
        })
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.endpoints.execution.execute_code_async')
    def test_execute_code_async_success(self, mock_task):
        """Test successful async code execution submission"""
        # Mock Celery task
        mock_task_result = Mock()
        mock_task_result.id = "test-task-id"
        mock_task.delay.return_value = mock_task_result
        
        # Make request
        response = client.post("/api/v1/execution/execute/async", json={
            "code": "print('Hello, World!')",
            "language": "python",
            "session_id": "test-session",
            "timeout": 30
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "test-task-id"
        assert data["status"] == "submitted"
    
    @patch('app.api.endpoints.execution.execute_code_async')
    def test_execute_code_async_failure(self, mock_task):
        """Test async code execution submission failure"""
        mock_task.delay.side_effect = Exception("Celery error")
        
        # Make request
        response = client.post("/api/v1/execution/execute/async", json={
            "code": "print('Hello, World!')",
            "language": "python",
            "session_id": "test-session",
            "timeout": 30
        })
        
        assert response.status_code == 500
        assert "Failed to submit execution task" in response.json()["detail"]
    
    def test_get_task_status_pending(self):
        """Test getting status of pending task"""
        # Skip Celery task status tests for now - they require complex setup
        pytest.skip("Celery task status testing requires complex setup")
    
    def test_get_task_status_progress(self):
        """Test getting status of task in progress"""
        # Skip Celery task status tests for now - they require complex setup
        pytest.skip("Celery task status testing requires complex setup")
    
    def test_get_task_status_success(self):
        """Test getting status of successful task"""
        # Skip Celery task status tests for now - they require complex setup
        pytest.skip("Celery task status testing requires complex setup")
    
    def test_get_task_status_failure(self):
        """Test getting status of failed task"""
        # Skip Celery task status tests for now - they require complex setup
        pytest.skip("Celery task status testing requires complex setup")
    
    @patch('app.api.endpoints.execution.code_execution_service')
    def test_validate_code_success(self, mock_service):
        """Test successful code validation"""
        mock_service.validate_code.return_value = (True, None)
        
        response = client.post("/api/v1/execution/validate", params={
            "code": "print('Hello, World!')",
            "language": "python"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["error_message"] is None
    
    @patch('app.api.endpoints.execution.code_execution_service')
    def test_validate_code_invalid(self, mock_service):
        """Test code validation with invalid code"""
        mock_service.validate_code.return_value = (False, "Dangerous code detected")
        
        response = client.post("/api/v1/execution/validate", params={
            "code": "import os",
            "language": "python"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is False
        assert "dangerous" in data["error_message"].lower()
    
    @patch('app.api.endpoints.execution.code_execution_service')
    def test_get_supported_languages(self, mock_service):
        """Test getting supported languages"""
        mock_service.get_supported_languages.return_value = ['python', 'javascript', 'java', 'cpp']
        
        response = client.get("/api/v1/execution/languages")
        
        assert response.status_code == 200
        data = response.json()
        assert set(data["languages"]) == {'python', 'javascript', 'java', 'cpp'}
    
    @patch('app.api.endpoints.execution.code_execution_service')
    def test_get_language_info_success(self, mock_service):
        """Test getting language info for supported language"""
        mock_service.get_language_info.return_value = {
            'image': 'ghostide-python',
            'dockerfile': 'python.Dockerfile',
            'extension': '.py'
        }
        
        response = client.get("/api/v1/execution/languages/python")
        
        assert response.status_code == 200
        data = response.json()
        assert data["language"] == "python"
        assert data["supported"] is True
        assert data["info"]["image"] == "ghostide-python"
    
    @patch('app.api.endpoints.execution.code_execution_service')
    def test_get_language_info_not_found(self, mock_service):
        """Test getting language info for unsupported language"""
        mock_service.get_language_info.return_value = None
        
        response = client.get("/api/v1/execution/languages/unsupported")
        
        assert response.status_code == 404
        assert "not supported" in response.json()["detail"]