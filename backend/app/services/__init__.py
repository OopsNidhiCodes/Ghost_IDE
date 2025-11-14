"""
Services module for GhostIDE backend
Contains business logic and external service integrations
"""

from .code_execution import CodeExecutionService, code_execution_service
from .celery_app import celery_app

__all__ = [
    'CodeExecutionService',
    'code_execution_service', 
    'celery_app'
]