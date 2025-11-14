"""
Code execution API endpoints
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, Request
from typing import Dict, List, Any
import uuid
import logging

from app.models.schemas import ExecutionRequest, ExecutionResult, ErrorResponse
from app.services.code_execution import code_execution_service
from app.services.websocket_code_execution import websocket_code_execution_service
from app.services.tasks import execute_code_async, validate_code_async
from app.middleware.auth import get_current_session, require_valid_session
from app.middleware.security import security_logger, rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/execute")
async def execute_code(request: ExecutionRequest) -> Dict[str, Any]:
    """
    Execute code synchronously
    
    This endpoint executes code immediately and returns the result.
    Use for quick executions or when immediate response is needed.
    """
    try:
        # Execute the code
        result = await code_execution_service.execute_code(
            request.code,
            request.language.value,
            request.input,
            request.timeout
        )
        
        return {
            "stdout": result.get("stdout", ""),
            "stderr": result.get("stderr", ""),
            "exit_code": result.get("exit_code", 0),
            "execution_time": result.get("execution_time", 0.0)
        }
    except Exception as e:
        logger.error(f"Code execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Code execution failed: {str(e)}"
        )


@router.post("/execute/websocket", response_model=ExecutionResult)
async def execute_code_with_websocket(request: ExecutionRequest) -> ExecutionResult:
    """
    Execute code with WebSocket notifications
    
    This endpoint executes code and sends real-time updates via WebSocket.
    Clients connected to the session's WebSocket will receive:
    - Execution start notification
    - Hook events (on_run, on_error)
    - Execution completion notification
    """
    try:
        result = await websocket_code_execution_service.execute_code_with_notifications(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"WebSocket code execution failed: {str(e)}"
        )


@router.post("/execute/async")
async def execute_code_async_endpoint(request: ExecutionRequest) -> Dict[str, str]:
    """
    Execute code asynchronously using Celery
    
    Returns a task ID that can be used to check execution status.
    Use for long-running code or when you want non-blocking execution.
    """
    try:
        # Convert request to dict for Celery serialization
        request_dict = request.model_dump()
        
        # Submit task to Celery
        task = execute_code_async.delay(request_dict)
        
        return {
            "task_id": task.id,
            "status": "submitted",
            "message": "Code execution task submitted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit execution task: {str(e)}"
        )


@router.get("/task/{task_id}")
async def get_task_status(task_id: str) -> Dict:
    """
    Get the status and result of an asynchronous execution task
    """
    try:
        from app.services.celery_app import celery_app
        
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            return {
                "task_id": task_id,
                "state": task.state,
                "status": "Task is waiting to be processed"
            }
        elif task.state == 'PROGRESS':
            return {
                "task_id": task_id,
                "state": task.state,
                "status": task.info.get('status', 'Processing...')
            }
        elif task.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "state": task.state,
                "result": task.result
            }
        else:  # FAILURE
            return {
                "task_id": task_id,
                "state": task.state,
                "error": str(task.info)
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.post("/validate")
async def validate_code(
    code: str, 
    language: str,
    http_request: Request,
    session: Dict = Depends(get_current_session)
) -> Dict[str, Any]:
    """
    Validate code without executing it
    
    Checks for basic security issues and language-specific requirements.
    """
    try:
        # Input sanitization
        from app.middleware.security import input_validator
        code = input_validator.sanitize_input(code, max_length=50000)
        language = input_validator.sanitize_input(language, max_length=20)
        
        # Log validation request
        client_ip = http_request.headers.get('X-Forwarded-For', http_request.client.host if http_request.client else 'unknown')
        security_logger.log_security_event(
            'CODE_VALIDATION_REQUEST',
            client_ip,
            {
                'session_id': session['session_id'],
                'language': language,
                'code_length': len(code)
            }
        )
        
        is_valid, error_msg = code_execution_service.validate_code(code, language)
        
        # Log validation failure
        if not is_valid:
            security_logger.log_input_validation_failure(
                client_ip,
                'CODE_VALIDATION',
                error_msg or 'Unknown validation error'
            )
        
        return {
            "is_valid": is_valid,
            "error_message": error_msg,
            "language": language
        }
    except Exception as e:
        logger.error(f"Code validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Code validation failed: {str(e)}"
        )


@router.get("/languages")
async def get_supported_languages() -> Dict[str, List[str]]:
    """
    Get list of supported programming languages
    """
    try:
        languages = code_execution_service.get_supported_languages()
        return {"languages": languages}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get supported languages: {str(e)}"
        )


@router.get("/languages/{language}")
async def get_language_info(language: str) -> Dict:
    """
    Get detailed information about a specific programming language
    """
    try:
        info = code_execution_service.get_language_info(language)
        if not info:
            raise HTTPException(
                status_code=404,
                detail=f"Language '{language}' is not supported"
            )
        
        return {
            "language": language,
            "info": info,
            "supported": True
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get language info: {str(e)}"
        )