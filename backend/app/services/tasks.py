"""
Celery tasks for GhostIDE
Handles asynchronous code execution
"""

import asyncio
from celery import current_task
from app.services.celery_app import celery_app
from app.services.code_execution import code_execution_service
from app.models.schemas import ExecutionRequest, ExecutionResult


@celery_app.task(bind=True)
def execute_code_async(self, execution_request_dict: dict) -> dict:
    """
    Asynchronous code execution task
    
    Args:
        execution_request_dict: Dictionary representation of ExecutionRequest
        
    Returns:
        Dictionary representation of ExecutionResult
    """
    try:
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={'status': 'Starting code execution...'}
        )
        
        # Convert dict to ExecutionRequest
        request = ExecutionRequest(**execution_request_dict)
        
        # Execute code synchronously (Docker operations are blocking)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                code_execution_service.execute_code(request)
            )
        finally:
            loop.close()
        
        # Convert result to dict for JSON serialization
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'exit_code': result.exit_code,
            'execution_time': result.execution_time,
            'status': 'completed'
        }
        
    except Exception as e:
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@celery_app.task
def validate_code_async(code: str, language: str) -> dict:
    """
    Asynchronous code validation task
    
    Args:
        code: Source code to validate
        language: Programming language
        
    Returns:
        Dictionary with validation result
    """
    try:
        is_valid, error_msg = code_execution_service.validate_code(code, language)
        
        return {
            'is_valid': is_valid,
            'error_message': error_msg,
            'status': 'completed'
        }
        
    except Exception as e:
        return {
            'is_valid': False,
            'error_message': f"Validation error: {str(e)}",
            'status': 'error'
        }


@celery_app.task
def get_supported_languages() -> dict:
    """
    Get supported programming languages
    
    Returns:
        Dictionary with supported languages
    """
    try:
        languages = code_execution_service.get_supported_languages()
        
        return {
            'languages': languages,
            'status': 'completed'
        }
        
    except Exception as e:
        return {
            'languages': [],
            'error': str(e),
            'status': 'error'
        }