"""
Code Execution Service for GhostIDE
Handles secure code execution in Docker containers
"""

import asyncio
import docker
import tempfile
import os
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path

from app.models.schemas import ExecutionRequest, ExecutionResult
from app.services.language_manager import language_manager, LanguageType

logger = logging.getLogger(__name__)


class CodeExecutionService:
    """Service for executing code in isolated Docker containers"""
    
    def __init__(self, skip_docker_init=False):
        """Initialize the code execution service"""
        self.language_manager = language_manager
        if skip_docker_init:
            self.docker_client = None
        else:
            try:
                self.docker_client = docker.from_env()
                self._ensure_images_built()
            except Exception as e:
                logger.warning(f"Docker not available: {e}")
                self.docker_client = None
    
    def _ensure_images_built(self):
        """Ensure all language Docker images are built"""
        if not self.docker_client:
            logger.warning("Docker client not available, skipping image build")
            return
            
        dockerfiles_path = Path(__file__).parent.parent.parent / "dockerfiles"
        
        # Use language manager to get supported languages
        for lang_key in self.language_manager.get_supported_languages():
            config = self.language_manager.get_language_config(lang_key)
            if not config:
                continue
                
            try:
                # Check if image exists
                self.docker_client.images.get(config.docker_image)
                logger.info(f"Docker image {config.docker_image} already exists")
            except docker.errors.ImageNotFound:
                logger.info(f"Building Docker image {config.docker_image}")
                try:
                    self.docker_client.images.build(
                        path=str(dockerfiles_path),
                        dockerfile=config.dockerfile,
                        tag=config.docker_image,
                        rm=True
                    )
                    logger.info(f"Successfully built {config.docker_image}")
                except Exception as e:
                    logger.error(f"Failed to build {config.docker_image}: {e}")
                    raise
    
    def validate_code(self, code: str, language: str) -> Tuple[bool, Optional[str]]:
        """
        Validate and sanitize user code using language manager and security checks
        Returns (is_valid, error_message)
        """
        # First use security middleware validation
        from app.middleware.security import input_validator
        security_valid, security_error = input_validator.validate_code(code, language)
        
        if not security_valid:
            return False, f"Security validation failed: {security_error}"
        
        # Then use language manager validation
        is_valid, issues = self.language_manager.validate_code(code, language)
        
        if not is_valid:
            # Return first error message
            error_issues = [issue for issue in issues if issue["severity"] == "error"]
            if error_issues:
                return False, error_issues[0]["message"]
            else:
                return False, "Code validation failed"
        
        return True, None
    
    async def execute_code(self, request: ExecutionRequest, trigger_hooks: bool = True) -> ExecutionResult:
        """
        Execute code in a Docker container
        
        Args:
            request: Code execution request
            trigger_hooks: Whether to trigger hook events (default: True)
        """
        start_time = datetime.now()
        
        # Trigger on_run hook if enabled
        if trigger_hooks:
            try:
                from .hook_manager import get_hook_manager
                hook_manager = get_hook_manager()
                if hook_manager:
                    await hook_manager.on_run_hook(
                        session_id=request.session_id,
                        code=request.code,
                        language=request.language.value
                    )
            except Exception as e:
                logger.warning(f"Failed to trigger on_run hook: {e}")
        
        # Check if Docker is available
        if not self.docker_client:
            result = ExecutionResult(
                stdout="",
                stderr="Docker is not available for code execution",
                exit_code=1,
                execution_time=0.0
            )
            
            # Trigger on_error hook if enabled
            if trigger_hooks:
                try:
                    from .hook_manager import get_hook_manager
                    hook_manager = get_hook_manager()
                    if hook_manager:
                        await hook_manager.on_error_hook(
                            session_id=request.session_id,
                            code=request.code,
                            language=request.language.value,
                            error=result.stderr
                        )
                except Exception as e:
                    logger.warning(f"Failed to trigger on_error hook: {e}")
            
            return result
        
        # Validate code first
        is_valid, error_msg = self.validate_code(request.code, request.language)
        if not is_valid:
            result = ExecutionResult(
                stdout="",
                stderr=error_msg,
                exit_code=1,
                execution_time=0.0
            )
            
            # Trigger on_error hook for validation errors
            if trigger_hooks:
                try:
                    from .hook_manager import get_hook_manager
                    hook_manager = get_hook_manager()
                    if hook_manager:
                        await hook_manager.on_error_hook(
                            session_id=request.session_id,
                            code=request.code,
                            language=request.language.value,
                            error=error_msg
                        )
                except Exception as e:
                    logger.warning(f"Failed to trigger on_error hook: {e}")
            
            return result
        
        # Get language configuration
        config = self.language_manager.get_language_config(request.language)
        if not config:
            result = ExecutionResult(
                stdout="",
                stderr=f"Unsupported language: {request.language}",
                exit_code=1,
                execution_time=0.0
            )
            
            # Trigger on_error hook for unsupported language
            if trigger_hooks:
                try:
                    from .hook_manager import get_hook_manager
                    hook_manager = get_hook_manager()
                    if hook_manager:
                        await hook_manager.on_error_hook(
                            session_id=request.session_id,
                            code=request.code,
                            language=request.language.value,
                            error=result.stderr
                        )
                except Exception as e:
                    logger.warning(f"Failed to trigger on_error hook: {e}")
            
            return result
        
        try:
            # Run code in Docker container with enhanced security configuration
            container = self.docker_client.containers.run(
                config.docker_image,
                stdin_open=True,
                stdout=True,
                stderr=True,
                detach=True,
                remove=True,
                mem_limit=config.compiler_config.memory_limit,
                cpu_quota=config.compiler_config.cpu_quota,
                network_disabled=True,  # No network access
                read_only=True,    # Read-only filesystem
                tmpfs={
                    '/tmp': 'rw,noexec,nosuid,nodev,size=50m',  # 50MB temp space with security flags
                    '/var/tmp': 'rw,noexec,nosuid,nodev,size=10m'  # Additional temp space
                },
                user='1000:1000',   # Non-root user
                # Additional security options
                cap_drop=['ALL'],  # Drop all capabilities
                security_opt=['no-new-privileges:true'],  # Prevent privilege escalation
                pids_limit=50,     # Limit number of processes
                ulimits=[
                    docker.types.Ulimit(name='nproc', soft=50, hard=50),  # Process limit
                    docker.types.Ulimit(name='nofile', soft=100, hard=100),  # File descriptor limit
                    docker.types.Ulimit(name='fsize', soft=10485760, hard=10485760),  # 10MB file size limit
                ],
                # Environment restrictions
                environment={
                    'PATH': '/usr/local/bin:/usr/bin:/bin',  # Restricted PATH
                    'HOME': '/tmp',  # Set home to temp directory
                    'USER': 'ghostuser',
                    'SHELL': '/bin/sh'
                },
                # Additional mount restrictions
                volumes={},  # No volume mounts
                working_dir='/tmp'  # Set working directory to temp
            )
            
            # Send code to container
            container_socket = container.attach_socket(
                params={'stdin': 1, 'stdout': 1, 'stderr': 1, 'stream': 1}
            )
            
            # Write code to stdin
            container_socket._sock.send(request.code.encode('utf-8'))
            container_socket._sock.shutdown(1)  # Close stdin
            
            # Wait for execution with timeout from language config
            timeout = min(request.timeout, config.compiler_config.timeout)
            try:
                exit_code = container.wait(timeout=timeout)['StatusCode']
            except Exception:
                # Timeout or other error
                container.kill()
                execution_time = (datetime.now() - start_time).total_seconds()
                result = ExecutionResult(
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds or failed",
                    exit_code=124,
                    execution_time=execution_time
                )
                
                # Trigger on_error hook for timeout
                if trigger_hooks:
                    try:
                        from .hook_manager import get_hook_manager
                        hook_manager = get_hook_manager()
                        if hook_manager:
                            await hook_manager.on_error_hook(
                                session_id=request.session_id,
                                code=request.code,
                                language=request.language.value,
                                error=result.stderr
                            )
                    except Exception as e:
                        logger.warning(f"Failed to trigger on_error hook: {e}")
                
                return result
            
            # Get output
            logs = container.logs(stdout=True, stderr=True, stream=False)
            output = logs.decode('utf-8', errors='replace')
            
            # Split stdout and stderr (simplified approach)
            stdout = output
            stderr = ""
            
            if exit_code != 0:
                stderr = output
                stdout = ""
                
                # Parse error message using language manager
                parsed_error = self.language_manager.parse_error_message(stderr, request.language)
                if parsed_error.get("formatted"):
                    stderr = parsed_error["formatted"]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            result = ExecutionResult(
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                execution_time=execution_time
            )
            
            # Trigger on_error hook if execution failed
            if trigger_hooks and exit_code != 0:
                try:
                    from .hook_manager import get_hook_manager
                    hook_manager = get_hook_manager()
                    if hook_manager:
                        await hook_manager.on_error_hook(
                            session_id=request.session_id,
                            code=request.code,
                            language=request.language.value,
                            error=stderr
                        )
                except Exception as e:
                    logger.warning(f"Failed to trigger on_error hook: {e}")
            
            return result
            
        except docker.errors.ContainerError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            result = ExecutionResult(
                stdout="",
                stderr=f"Container error: {str(e)}",
                exit_code=1,
                execution_time=execution_time
            )
            
            # Trigger on_error hook for container errors
            if trigger_hooks:
                try:
                    from .hook_manager import get_hook_manager
                    hook_manager = get_hook_manager()
                    if hook_manager:
                        await hook_manager.on_error_hook(
                            session_id=request.session_id,
                            code=request.code,
                            language=request.language.value,
                            error=result.stderr
                        )
                except Exception as e:
                    logger.warning(f"Failed to trigger on_error hook: {e}")
            
            return result
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Code execution error: {e}")
            result = ExecutionResult(
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                execution_time=execution_time
            )
            
            # Trigger on_error hook for general execution errors
            if trigger_hooks:
                try:
                    from .hook_manager import get_hook_manager
                    hook_manager = get_hook_manager()
                    if hook_manager:
                        await hook_manager.on_error_hook(
                            session_id=request.session_id,
                            code=request.code,
                            language=request.language.value,
                            error=result.stderr
                        )
                except Exception as e:
                    logger.warning(f"Failed to trigger on_error hook: {e}")
            
            return result
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported programming languages"""
        return self.language_manager.get_supported_languages()
    
    def get_language_info(self, language: str) -> Optional[Dict]:
        """Get information about a specific language"""
        config = self.language_manager.get_language_config(language)
        if not config:
            return None
        
        return {
            "name": config.name,
            "extension": config.extension,
            "monaco_language": config.monaco_language,
            "icon": config.icon,
            "color": config.color,
            "template": config.template,
            "examples": config.examples
        }
    
    def detect_language_from_file(self, filename: str, content: str = "") -> Optional[str]:
        """Detect programming language from filename and/or content"""
        # Try filename first
        detected = self.language_manager.detect_language_from_filename(filename)
        if detected:
            return detected
        
        # Try content if available
        if content:
            return self.language_manager.detect_language_from_content(content)
        
        return None
    
    def get_language_template(self, language: str) -> Optional[str]:
        """Get template code for a specific language"""
        return self.language_manager.get_language_template(language)
    
    def get_language_examples(self, language: str) -> List[Dict[str, str]]:
        """Get example code snippets for a specific language"""
        return self.language_manager.get_language_examples(language)
    
    def validate_code_detailed(self, code: str, language: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Get detailed validation results including warnings"""
        return self.language_manager.validate_code(code, language)


# Global instance
code_execution_service = CodeExecutionService()