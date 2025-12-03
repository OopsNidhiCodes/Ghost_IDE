"""
Code Execution Service for GhostIDE
Handles secure code execution in Docker containers
"""

import asyncio
import subprocess
import sys
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
            # Try to connect to Docker using CLI verification
            try:
                result = subprocess.run(['docker', 'version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    # Docker CLI works, but Python SDK might not
                    # We'll use subprocess for execution instead
                    self.docker_client = "cli"  # Use CLI mode
                    logger.info("Docker available via CLI")
                else:
                    self.docker_client = None
                    logger.warning("Docker not available")
            except (FileNotFoundError, subprocess.TimeoutExpired, Exception) as e:
                logger.warning(f"Docker not available: {e}")
                self.docker_client = None
    
    def _ensure_images_built(self):
        """Ensure all language Docker images are built - CLI mode only checks existence"""
        if not self.docker_client:
            logger.warning("Docker client not available, skipping image check")
            return
            
        # In CLI mode, we just check if images exist
        # Build should be done via build_containers.py script
        for lang_key in self.language_manager.get_supported_languages():
            config = self.language_manager.get_language_config(lang_key)
            if not config:
                continue
                
            try:
                result = subprocess.run(
                    ['docker', 'images', '-q', config.docker_image],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    logger.info(f"Docker image {config.docker_image} exists")
                else:
                    logger.warning(f"Docker image {config.docker_image} not found. Run scripts/build_containers.py")
            except Exception as e:
                logger.error(f"Failed to check image {config.docker_image}: {e}")
    
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
    
    def _get_execution_script(self, language: str, extension: str) -> str:
        """Generate the shell script to execute code based on language"""
        lang = language.value if hasattr(language, 'value') else str(language).lower()
        
        if lang == 'python':
            return f'cat > code{extension} && python3 -u code{extension}'
        elif lang == 'javascript':
            return f'cat > code{extension} && node code{extension}'
        elif lang == 'cpp':
            return f'cat > code{extension} && g++ -o main code{extension} -std=c++17 && ./main'
        elif lang == 'java':
            return f'cat > Main.java && javac Main.java && java Main'
        else:
            return f'cat > code{extension} && python3 -u code{extension}'
    
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
        
        # Check if Docker is available - use native execution as fallback
        if not self.docker_client:
            logger.info("Docker not available, using native execution mode")
            
            lang_str = request.language.value if hasattr(request.language, 'value') else str(request.language)
            
            # Try native execution for all supported languages
            try:
                result = await self._native_execution(request, start_time)
                
                # Trigger on_error hook if execution failed
                if trigger_hooks and result.exit_code != 0:
                    try:
                        from .hook_manager import get_hook_manager
                        hook_manager = get_hook_manager()
                        if hook_manager:
                            await hook_manager.on_error_hook(
                                session_id=request.session_id,
                                code=request.code,
                                language=lang_str,
                                error=result.stderr
                            )
                    except Exception as e:
                        logger.warning(f"Failed to trigger on_error hook: {e}")
                
                return result
            except Exception as e:
                logger.error(f"Native execution failed: {e}", exc_info=True)
                result = ExecutionResult(
                    stdout="",
                    stderr=f"Execution error: {str(e)}",
                    exit_code=1,
                    execution_time=0.0
                )
                
                # Trigger on_error hook
                if trigger_hooks:
                    try:
                        from .hook_manager import get_hook_manager
                        hook_manager = get_hook_manager()
                        if hook_manager:
                            await hook_manager.on_error_hook(
                                session_id=request.session_id,
                                code=request.code,
                                language=lang_str,
                                error=result.stderr
                            )
                    except Exception as e:
                        logger.warning(f"Failed to trigger on_error hook: {e}")
                
                return result
                
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
            # Run code in Docker container using CLI
            timeout = min(request.timeout, config.compiler_config.timeout)
            
            # Set PATH based on language (Java needs special path)
            lang = request.language.value if hasattr(request.language, 'value') else str(request.language).lower()
            if lang == 'java':
                path_env = '/opt/java/openjdk/bin:/usr/local/bin:/usr/bin:/bin'
                # Java needs more resources
                pids_limit = 100
                nproc_limit = '100:100'
            else:
                path_env = '/usr/local/bin:/usr/bin:/bin'
                pids_limit = 50
                nproc_limit = '50:50'
            
            # Prepare Docker run command with security settings
            docker_cmd = [
                'docker', 'run',
                '--rm',  # Remove container after execution
                '-i',    # Interactive mode for stdin
                f'--memory={config.compiler_config.memory_limit}',
                f'--cpus={config.compiler_config.cpu_quota / 100000}',
                '--network=none',  # No network access
                '--tmpfs=/tmp:rw,exec,nosuid,nodev,size=50m',  # Allow exec for compiled binaries
                '--user=1000:1000',  # Non-root user
                '--cap-drop=ALL',    # Drop all capabilities
                '--security-opt=no-new-privileges:true',
                f'--pids-limit={pids_limit}',
                f'--ulimit=nproc={nproc_limit}',
                '--ulimit=nofile=100:100',
                '--ulimit=fsize=10485760:10485760',
                '-e', f'PATH={path_env}',
                '-e', 'HOME=/tmp',
                '-w', '/tmp',
                config.docker_image,
                'sh', '-c',
                self._get_execution_script(request.language, config.extension)
            ]
            
            # Execute with timeout using subprocess.run for Windows compatibility
            try:
                result_subprocess = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: subprocess.run(
                        docker_cmd,
                        input=request.code.encode('utf-8'),
                        capture_output=True,
                        timeout=timeout
                    )
                )
                
                stdout = result_subprocess.stdout.decode('utf-8', errors='replace')
                stderr = result_subprocess.stderr.decode('utf-8', errors='replace')
                exit_code = result_subprocess.returncode
                        
            except subprocess.TimeoutExpired:
                execution_time = (datetime.now() - start_time).total_seconds()
                result = ExecutionResult(
                    stdout="",
                    stderr=f"Execution timed out after {timeout} seconds",
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
            
            # Parse error message if execution failed
            if exit_code != 0 and stderr:
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
            
        except FileNotFoundError as e:
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
            logger.error(f"Code execution error: {e}", exc_info=True)
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
    
    async def _fallback_python_execution(self, request: ExecutionRequest, start_time: datetime) -> ExecutionResult:
        """
        Fallback Python execution without Docker (for development only)
        WARNING: This is NOT secure and should only be used in development!
        """
        return await self._native_execution(request, start_time)
    
    async def _native_execution(self, request: ExecutionRequest, start_time: datetime) -> ExecutionResult:
        """
        Native execution for all languages without Docker.
        Used in production environments where Docker-in-Docker is not available.
        """
        import subprocess
        import sys
        
        lang_str = request.language.value if hasattr(request.language, 'value') else str(request.language)
        lang_lower = lang_str.lower()
        
        try:
            # Determine file extension and execution command based on language
            exec_config = {
                'python': {'ext': '.py', 'cmd': lambda f: [sys.executable, f]},
                'javascript': {'ext': '.js', 'cmd': lambda f: ['node', f]},
                'java': {'ext': '.java', 'cmd': None, 'compile': True},
                'cpp': {'ext': '.cpp', 'cmd': None, 'compile': True},
            }
            
            config = exec_config.get(lang_lower)
            if not config:
                return ExecutionResult(
                    stdout="",
                    stderr=f"Unsupported language: {lang_str}",
                    exit_code=1,
                    execution_time=0.0
                )
            
            # Create temp directory for execution
            temp_dir = tempfile.mkdtemp(prefix='ghostide_')
            
            try:
                timeout = min(request.timeout, 30)
                
                if lang_lower == 'java':
                    # Extract class name from code
                    import re
                    class_match = re.search(r'public\s+class\s+(\w+)', request.code)
                    class_name = class_match.group(1) if class_match else 'Main'
                    
                    # Write Java file
                    java_file = os.path.join(temp_dir, f'{class_name}.java')
                    with open(java_file, 'w', encoding='utf-8') as f:
                        f.write(request.code)
                    
                    # Compile
                    compile_proc = await asyncio.create_subprocess_exec(
                        'javac', java_file,
                        cwd=temp_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    _, compile_err = await asyncio.wait_for(compile_proc.communicate(), timeout=timeout)
                    
                    if compile_proc.returncode != 0:
                        return ExecutionResult(
                            stdout="",
                            stderr=f"Compilation error:\n{compile_err.decode('utf-8', errors='replace')}",
                            exit_code=1,
                            execution_time=(datetime.now() - start_time).total_seconds()
                        )
                    
                    # Execute
                    cmd = ['java', '-cp', temp_dir, class_name]
                    
                elif lang_lower == 'cpp':
                    # Write C++ file
                    cpp_file = os.path.join(temp_dir, 'main.cpp')
                    exe_file = os.path.join(temp_dir, 'main')
                    
                    with open(cpp_file, 'w', encoding='utf-8') as f:
                        f.write(request.code)
                    
                    # Compile
                    compile_proc = await asyncio.create_subprocess_exec(
                        'g++', '-std=c++17', '-o', exe_file, cpp_file,
                        cwd=temp_dir,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    _, compile_err = await asyncio.wait_for(compile_proc.communicate(), timeout=timeout)
                    
                    if compile_proc.returncode != 0:
                        return ExecutionResult(
                            stdout="",
                            stderr=f"Compilation error:\n{compile_err.decode('utf-8', errors='replace')}",
                            exit_code=1,
                            execution_time=(datetime.now() - start_time).total_seconds()
                        )
                    
                    cmd = [exe_file]
                    
                else:
                    # Python or JavaScript - write file and get command
                    temp_file = os.path.join(temp_dir, f'code{config["ext"]}')
                    with open(temp_file, 'w', encoding='utf-8') as f:
                        f.write(request.code)
                    cmd = config['cmd'](temp_file)
                
                # Execute the code
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=temp_dir,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdin_data = request.input.encode('utf-8') if request.input else None
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(input=stdin_data),
                        timeout=timeout
                    )
                    exit_code = process.returncode
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    return ExecutionResult(
                        stdout="",
                        stderr=f"Execution timed out after {timeout} seconds",
                        exit_code=124,
                        execution_time=(datetime.now() - start_time).total_seconds(),
                        timed_out=True
                    )
                
                return ExecutionResult(
                    stdout=stdout.decode('utf-8', errors='replace'),
                    stderr=stderr.decode('utf-8', errors='replace'),
                    exit_code=exit_code or 0,
                    execution_time=(datetime.now() - start_time).total_seconds()
                )
                
            finally:
                # Clean up temp directory
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                    
        except FileNotFoundError as e:
            # Language runtime not installed
            return ExecutionResult(
                stdout="",
                stderr=f"Runtime not available: {str(e)}. Please ensure {lang_str} is installed.",
                exit_code=1,
                execution_time=(datetime.now() - start_time).total_seconds()
            )
        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr=f"Execution error: {str(e)}",
                exit_code=1,
                execution_time=(datetime.now() - start_time).total_seconds()
            )


# Global instance
class _CodeExecutionServiceProxy:
    """Lazy proxy so tests can patch the service easily."""

    def __init__(self):
        self._instance: Optional[CodeExecutionService] = None
        self._class_token = CodeExecutionService

    def _ensure_instance(self) -> CodeExecutionService:
        current_cls = CodeExecutionService
        if self._instance is None or current_cls is not self._class_token:
            enable_docker = os.getenv("ENABLE_DOCKER_EXECUTION", "").lower() in ("1", "true", "yes")
            self._instance = current_cls(skip_docker_init=not enable_docker)
            self._class_token = current_cls
        return self._instance

    def __getattr__(self, item):
        return getattr(self._ensure_instance(), item)

    def set_instance(self, instance: CodeExecutionService):
        self._instance = instance
        if instance is not None:
            self._class_token = instance.__class__


code_execution_service = _CodeExecutionServiceProxy()


def get_code_execution_service() -> CodeExecutionService:
    """Retrieve the underlying code execution service instance."""
    return code_execution_service._ensure_instance()