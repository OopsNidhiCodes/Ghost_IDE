"""
Unit tests for code execution service
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
import docker

from app.services.code_execution import CodeExecutionService
from app.models.schemas import ExecutionRequest, ExecutionResult


class TestCodeExecutionService:
    """Test cases for CodeExecutionService"""
    
    @pytest.fixture
    def service(self):
        """Create a CodeExecutionService instance for testing"""
        # Create service without Docker initialization
        service = CodeExecutionService(skip_docker_init=True)
        
        # Mock Docker client
        mock_client = Mock()
        mock_client.images.get.side_effect = docker.errors.ImageNotFound("Image not found")
        mock_client.images.build.return_value = Mock()
        service.docker_client = mock_client
        
        return service
    
    def test_supported_languages(self, service):
        """Test that all expected languages are supported"""
        languages = service.get_supported_languages()
        expected = ['python', 'javascript', 'java', 'cpp']
        assert set(languages) == set(expected)
    
    def test_get_language_info(self, service):
        """Test getting language configuration info"""
        python_info = service.get_language_info('python')
        assert python_info is not None
        assert python_info['image'] == 'ghostide-python'
        assert python_info['extension'] == '.py'
        
        # Test unsupported language
        invalid_info = service.get_language_info('invalid')
        assert invalid_info is None
    
    def test_validate_code_empty(self, service):
        """Test validation of empty code"""
        is_valid, error = service.validate_code("", "python")
        assert not is_valid
        assert "empty" in error.lower()
    
    def test_validate_code_unsupported_language(self, service):
        """Test validation with unsupported language"""
        is_valid, error = service.validate_code("print('hello')", "unsupported")
        assert not is_valid
        assert "unsupported language" in error.lower()
    
    def test_validate_code_too_large(self, service):
        """Test validation of code that's too large"""
        large_code = "x = 'a' * 10000\n" * 5000  # Very large code (>50KB)
        is_valid, error = service.validate_code(large_code, "python")
        assert not is_valid
        assert "too large" in error.lower()
    
    def test_validate_code_dangerous_imports(self, service):
        """Test validation catches dangerous Python imports"""
        dangerous_codes = [
            "import os\nos.system('rm -rf /')",
            "import subprocess\nsubprocess.call(['ls'])",
            "eval('print(1)')",
            "exec('print(1)')",
            "open('/etc/passwd', 'r')"
        ]
        
        for code in dangerous_codes:
            is_valid, error = service.validate_code(code, "python")
            assert not is_valid
            assert "dangerous" in error.lower()
    
    def test_validate_code_java_missing_main(self, service):
        """Test Java validation requires Main class"""
        java_code = "public class Test { }"
        is_valid, error = service.validate_code(java_code, "java")
        assert not is_valid
        assert "Main" in error
    
    def test_validate_code_valid(self, service):
        """Test validation of valid code"""
        valid_codes = {
            "python": "print('Hello, World!')",
            "javascript": "console.log('Hello, World!');",
            "java": "public class Main { public static void main(String[] args) { System.out.println(\"Hello\"); } }",
            "cpp": "#include <iostream>\nint main() { std::cout << \"Hello\"; return 0; }"
        }
        
        for language, code in valid_codes.items():
            is_valid, error = service.validate_code(code, language)
            assert is_valid
            assert error is None
    
    @pytest.mark.asyncio
    async def test_execute_code_invalid_language(self, service):
        """Test execution with invalid language"""
        # Test with direct service call bypassing Pydantic validation
        result = await service.execute_code(Mock(
            code="print('hello')",
            language="invalid",
            session_id="test-session",
            timeout=30
        ))
        
        assert result.exit_code == 1
        assert "unsupported language" in result.stderr.lower()
    
    @pytest.mark.asyncio
    async def test_execute_code_invalid_code(self, service):
        """Test execution with invalid code"""
        request = ExecutionRequest(
            code="import os",
            language="python",
            session_id="test-session",
            timeout=30
        )
        
        result = await service.execute_code(request)
        assert result.exit_code == 1
        assert "dangerous" in result.stderr.lower()
    
    @pytest.mark.asyncio
    async def test_execute_code_success(self, service):
        """Test successful code execution"""
        # Mock Docker container execution
        mock_container = Mock()
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Hello, World!\n"
        mock_container.attach_socket.return_value._sock = Mock()
        
        service.docker_client.containers.run.return_value = mock_container
        
        request = ExecutionRequest(
            code="print('Hello, World!')",
            language="python",
            session_id="test-session",
            timeout=30
        )
        
        result = await service.execute_code(request)
        assert result.exit_code == 0
        assert "Hello, World!" in result.stdout
        assert result.execution_time >= 0
    
    @pytest.mark.asyncio
    async def test_execute_code_timeout(self, service):
        """Test code execution timeout"""
        # Mock Docker container that times out
        mock_container = Mock()
        mock_container.wait.side_effect = Exception("Timeout")
        mock_container.kill.return_value = None
        
        service.docker_client.containers.run.return_value = mock_container
        
        request = ExecutionRequest(
            code="while True: pass",  # Infinite loop
            language="python",
            session_id="test-session",
            timeout=1
        )
        
        result = await service.execute_code(request)
        assert result.exit_code == 124  # Timeout exit code
        assert "timed out" in result.stderr.lower()
    
    @pytest.mark.asyncio
    async def test_execute_code_container_error(self, service):
        """Test handling of Docker container errors"""
        service.docker_client.containers.run.side_effect = docker.errors.ContainerError(
            container="test",
            exit_status=1,
            command="python",
            image="ghostide-python",
            stderr=b"Container error"
        )
        
        request = ExecutionRequest(
            code="print('hello')",
            language="python",
            session_id="test-session",
            timeout=30
        )
        
        result = await service.execute_code(request)
        assert result.exit_code == 1
        assert "container error" in result.stderr.lower()


class TestCodeExecutionIntegration:
    """Integration tests for code execution (requires Docker)"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_python_execution(self):
        """Test real Python code execution (requires Docker)"""
        service = CodeExecutionService()
        
        request = ExecutionRequest(
            code="print('Hello from Python!')\nprint(2 + 2)",
            language="python",
            session_id="integration-test",
            timeout=30
        )
        
        result = await service.execute_code(request)
        assert result.exit_code == 0
        assert "Hello from Python!" in result.stdout
        assert "4" in result.stdout
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_javascript_execution(self):
        """Test real JavaScript code execution (requires Docker)"""
        service = CodeExecutionService()
        
        request = ExecutionRequest(
            code="console.log('Hello from JavaScript!');\nconsole.log(2 + 2);",
            language="javascript",
            session_id="integration-test",
            timeout=30
        )
        
        result = await service.execute_code(request)
        assert result.exit_code == 0
        assert "Hello from JavaScript!" in result.stdout
        assert "4" in result.stdout