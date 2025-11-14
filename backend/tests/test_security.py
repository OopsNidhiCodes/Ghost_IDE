"""
Security tests for GhostIDE
Tests input validation, rate limiting, and container isolation
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.main import app
from app.middleware.security import (
    InputValidator, 
    RateLimiter, 
    SecurityLogger,
    SecurityMiddleware
)
from app.middleware.auth import SessionManager, JWTManager
from app.services.code_execution import CodeExecutionService
from app.models.schemas import ExecutionRequest, LanguageType


class TestInputValidator:
    """Test input validation and sanitization"""
    
    def setup_method(self):
        self.validator = InputValidator()
    
    def test_validate_python_code_safe(self):
        """Test validation of safe Python code"""
        safe_code = """
def hello_world():
    print("Hello, World!")
    return 42

hello_world()
"""
        is_valid, error = self.validator.validate_code(safe_code, "python")
        assert is_valid is True
        assert error is None
    
    def test_validate_python_code_dangerous_import(self):
        """Test validation rejects dangerous imports"""
        dangerous_code = """
import os
os.system("rm -rf /")
"""
        is_valid, error = self.validator.validate_code(dangerous_code, "python")
        assert is_valid is False
        assert "os" in error.lower()
    
    def test_validate_python_code_dangerous_function(self):
        """Test validation rejects dangerous functions"""
        dangerous_code = """
exec("print('hacked')")
"""
        is_valid, error = self.validator.validate_code(dangerous_code, "python")
        assert is_valid is False
        assert "exec" in error.lower()
    
    def test_validate_javascript_code_safe(self):
        """Test validation of safe JavaScript code"""
        safe_code = """
function helloWorld() {
    console.log("Hello, World!");
    return 42;
}

helloWorld();
"""
        is_valid, error = self.validator.validate_code(safe_code, "javascript")
        assert is_valid is True
        assert error is None
    
    def test_validate_javascript_code_dangerous_require(self):
        """Test validation rejects require statements"""
        dangerous_code = """
const fs = require('fs');
fs.unlinkSync('/etc/passwd');
"""
        is_valid, error = self.validator.validate_code(dangerous_code, "javascript")
        assert is_valid is False
        assert "require" in error.lower()
    
    def test_validate_code_too_long(self):
        """Test validation rejects code that's too long"""
        long_code = "x = 1\n" * 25001  # Over 50KB
        is_valid, error = self.validator.validate_code(long_code, "python")
        assert is_valid is False
        assert "maximum length" in error.lower()
    
    def test_sanitize_input_basic(self):
        """Test basic input sanitization"""
        dirty_input = '<script>alert("xss")</script>Hello World'
        clean_input = self.validator.sanitize_input(dirty_input)
        assert "<script>" not in clean_input
        assert "Hello World" in clean_input
    
    def test_sanitize_input_length_limit(self):
        """Test input length limiting"""
        long_input = "A" * 2000
        clean_input = self.validator.sanitize_input(long_input, max_length=100)
        assert len(clean_input) <= 100


class TestRateLimiter:
    """Test rate limiting functionality"""
    
    def setup_method(self):
        self.rate_limiter = RateLimiter()
    
    def test_rate_limit_within_bounds(self):
        """Test requests within rate limits are allowed"""
        client_ip = "192.168.1.1"
        
        # Make requests within limit
        for i in range(5):
            assert self.rate_limiter.is_allowed(client_ip, 'code_execution') is True
    
    def test_rate_limit_exceeded(self):
        """Test rate limit enforcement"""
        client_ip = "192.168.1.2"
        
        # Exceed rate limit
        for i in range(15):  # Limit is 10 for code_execution
            result = self.rate_limiter.is_allowed(client_ip, 'code_execution')
            if i < 10:
                assert result is True
            else:
                assert result is False
    
    def test_rate_limit_different_endpoints(self):
        """Test different rate limits for different endpoints"""
        client_ip = "192.168.1.3"
        
        # Test API requests (higher limit)
        for i in range(50):
            assert self.rate_limiter.is_allowed(client_ip, 'api_requests') is True
        
        # Should still be blocked for code execution after exceeding that limit
        for i in range(15):
            result = self.rate_limiter.is_allowed(client_ip, 'code_execution')
            if i < 10:
                assert result is True
            else:
                assert result is False
    
    def test_rate_limit_cleanup(self):
        """Test that old requests are cleaned up"""
        client_ip = "192.168.1.4"
        
        # Fill up the rate limit
        for i in range(10):
            self.rate_limiter.is_allowed(client_ip, 'code_execution')
        
        # Manually clean old requests (simulate time passing)
        key = f"{client_ip}:code_execution"
        cutoff = datetime.now() - timedelta(minutes=2)
        while self.rate_limiter.requests[key]:
            self.rate_limiter.requests[key].popleft()
        
        # Should be able to make requests again
        assert self.rate_limiter.is_allowed(client_ip, 'code_execution') is True


class TestSessionManager:
    """Test session management"""
    
    def setup_method(self):
        self.session_manager = SessionManager()
    
    def test_create_session(self):
        """Test session creation"""
        session_id = "test_session_123"
        client_ip = "192.168.1.1"
        
        session = self.session_manager.create_session(session_id, client_ip)
        
        assert session['session_id'] == session_id
        assert session['client_ip'] == client_ip
        assert session['is_authenticated'] is False
        assert 'created_at' in session
        assert 'last_activity' in session
    
    def test_get_valid_session(self):
        """Test retrieving valid session"""
        session_id = "test_session_456"
        client_ip = "192.168.1.2"
        
        # Create session
        self.session_manager.create_session(session_id, client_ip)
        
        # Retrieve session
        session = self.session_manager.get_session(session_id)
        assert session is not None
        assert session['session_id'] == session_id
    
    def test_get_expired_session(self):
        """Test that expired sessions are cleaned up"""
        session_id = "test_session_789"
        client_ip = "192.168.1.3"
        
        # Create session
        session = self.session_manager.create_session(session_id, client_ip)
        
        # Manually expire session
        session['last_activity'] = datetime.now() - timedelta(hours=3)
        
        # Should return None for expired session
        result = self.session_manager.get_session(session_id)
        assert result is None
        assert session_id not in self.session_manager.active_sessions
    
    def test_update_session_activity(self):
        """Test session activity updates"""
        session_id = "test_session_activity"
        client_ip = "192.168.1.4"
        
        # Create session
        original_session = self.session_manager.create_session(session_id, client_ip)
        original_activity = original_session['last_activity']
        original_count = original_session['request_count']
        
        # Wait a bit and update activity
        time.sleep(0.1)
        result = self.session_manager.update_session_activity(session_id)
        
        assert result is True
        updated_session = self.session_manager.get_session(session_id)
        assert updated_session['last_activity'] > original_activity
        assert updated_session['request_count'] == original_count + 1


class TestJWTManager:
    """Test JWT token management"""
    
    def setup_method(self):
        self.jwt_manager = JWTManager()
    
    def test_create_and_verify_token(self):
        """Test token creation and verification"""
        session_id = "test_jwt_session"
        client_ip = "192.168.1.1"
        
        # Create token
        token = self.jwt_manager.create_token(session_id, client_ip)
        assert token is not None
        assert isinstance(token, str)
        
        # Verify token
        payload = self.jwt_manager.verify_token(token, client_ip)
        assert payload is not None
        assert payload['session_id'] == session_id
        assert payload['client_ip'] == client_ip
    
    def test_verify_token_wrong_ip(self):
        """Test token verification fails with wrong IP"""
        session_id = "test_jwt_session_ip"
        client_ip = "192.168.1.1"
        wrong_ip = "192.168.1.2"
        
        # Create token
        token = self.jwt_manager.create_token(session_id, client_ip)
        
        # Verify with wrong IP
        payload = self.jwt_manager.verify_token(token, wrong_ip)
        assert payload is None
    
    def test_verify_invalid_token(self):
        """Test verification of invalid token"""
        client_ip = "192.168.1.1"
        invalid_token = "invalid.jwt.token"
        
        payload = self.jwt_manager.verify_token(invalid_token, client_ip)
        assert payload is None


class TestCodeExecutionSecurity:
    """Test code execution security measures"""
    
    def setup_method(self):
        self.code_service = CodeExecutionService(skip_docker_init=True)
    
    def test_validate_safe_code(self):
        """Test validation of safe code"""
        safe_code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(fibonacci(10))
"""
        is_valid, error = self.code_service.validate_code(safe_code, "python")
        assert is_valid is True
        assert error is None
    
    def test_validate_dangerous_code(self):
        """Test validation rejects dangerous code"""
        dangerous_code = """
import subprocess
subprocess.call(['rm', '-rf', '/'])
"""
        is_valid, error = self.code_service.validate_code(dangerous_code, "python")
        assert is_valid is False
        assert error is not None
    
    @patch('docker.from_env')
    def test_docker_security_configuration(self, mock_docker):
        """Test Docker container security configuration"""
        # Mock Docker client and container
        mock_client = Mock()
        mock_container = Mock()
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Hello World"
        mock_client.containers.run.return_value = mock_container
        mock_docker.return_value = mock_client
        
        # Create service with mocked Docker
        service = CodeExecutionService()
        service.docker_client = mock_client
        
        # Create execution request
        request = ExecutionRequest(
            code="print('Hello World')",
            language=LanguageType.PYTHON,
            session_id="test_session"
        )
        
        # Execute code (this will call the mocked Docker)
        asyncio.run(service.execute_code(request))
        
        # Verify security configuration was applied
        mock_client.containers.run.assert_called_once()
        call_args = mock_client.containers.run.call_args
        
        # Check security parameters
        assert call_args[1]['network_disabled'] is True
        assert call_args[1]['read_only'] is True
        assert call_args[1]['user'] == '1000:1000'
        assert 'tmpfs' in call_args[1]
        assert call_args[1]['cap_drop'] == ['ALL']
        assert 'no-new-privileges:true' in call_args[1]['security_opt']


class TestSecurityIntegration:
    """Integration tests for security features"""
    
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_rate_limiting_integration(self):
        """Test rate limiting in API endpoints"""
        # This would require setting up test client with proper session
        # For now, we'll test the middleware components individually
        pass
    
    def test_input_validation_integration(self):
        """Test input validation in API endpoints"""
        # Test with dangerous code
        dangerous_payload = {
            "code": "import os; os.system('rm -rf /')",
            "language": "python",
            "session_id": "test_session"
        }
        
        # This would fail without proper session setup
        # The actual integration test would need proper authentication
        pass
    
    def test_security_headers(self):
        """Test security headers are added to responses"""
        response = self.client.get("/health")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-Frame-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"


if __name__ == "__main__":
    pytest.main([__file__])