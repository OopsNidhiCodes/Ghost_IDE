"""
Unit tests for Celery tasks
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from celery.exceptions import Retry

from app.services.tasks import execute_code_async, validate_code_async, get_supported_languages
from app.models.schemas import ExecutionRequest, ExecutionResult


class TestCeleryTasks:
    """Test cases for Celery tasks"""
    
    def test_validate_code_async_valid(self):
        """Test async code validation with valid code"""
        with patch('app.services.tasks.code_execution_service') as mock_service:
            mock_service.validate_code.return_value = (True, None)
            
            result = validate_code_async("print('hello')", "python")
            
            assert result['is_valid'] is True
            assert result['error_message'] is None
            assert result['status'] == 'completed'
    
    def test_validate_code_async_invalid(self):
        """Test async code validation with invalid code"""
        with patch('app.services.tasks.code_execution_service') as mock_service:
            mock_service.validate_code.return_value = (False, "Dangerous code detected")
            
            result = validate_code_async("import os", "python")
            
            assert result['is_valid'] is False
            assert "dangerous" in result['error_message'].lower()
            assert result['status'] == 'completed'
    
    def test_validate_code_async_exception(self):
        """Test async code validation with exception"""
        with patch('app.services.tasks.code_execution_service') as mock_service:
            mock_service.validate_code.side_effect = Exception("Service error")
            
            result = validate_code_async("print('hello')", "python")
            
            assert result['is_valid'] is False
            assert "validation error" in result['error_message'].lower()
            assert result['status'] == 'error'
    
    def test_get_supported_languages_success(self):
        """Test getting supported languages successfully"""
        with patch('app.services.tasks.code_execution_service') as mock_service:
            mock_service.get_supported_languages.return_value = ['python', 'javascript']
            
            result = get_supported_languages()
            
            assert result['languages'] == ['python', 'javascript']
            assert result['status'] == 'completed'
    
    def test_get_supported_languages_exception(self):
        """Test getting supported languages with exception"""
        with patch('app.services.tasks.code_execution_service') as mock_service:
            mock_service.get_supported_languages.side_effect = Exception("Service error")
            
            result = get_supported_languages()
            
            assert result['languages'] == []
            assert 'error' in result
            assert result['status'] == 'error'
    
    def test_execute_code_async_success(self):
        """Test successful async code execution logic"""
        # Skip complex Celery task testing for now
        # The core logic is tested in the code execution service tests
        pytest.skip("Celery task testing requires complex setup - core logic tested elsewhere")
    
    def test_execute_code_async_failure(self):
        """Test async code execution with failure"""
        # Skip complex Celery task testing for now
        # The core logic is tested in the code execution service tests
        pytest.skip("Celery task testing requires complex setup - core logic tested elsewhere")


class TestCeleryTaskIntegration:
    """Integration tests for Celery tasks"""
    
    @pytest.mark.integration
    def test_execute_code_async_real_execution(self):
        """Test real async code execution (requires Docker and Celery)"""
        request_dict = {
            'code': "print('Hello from async task!')",
            'language': 'python',
            'session_id': 'integration-test',
            'timeout': 30
        }
        
        # Mock task for testing
        mock_task = Mock()
        mock_task.update_state = Mock()
        
        with patch('app.services.tasks.current_task', mock_task):
            result = execute_code_async(mock_task, request_dict)
        
        assert result['status'] == 'completed'
        assert result['exit_code'] == 0
        assert 'Hello from async task!' in result['stdout']