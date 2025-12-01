"""
WebSocket-enabled Code Execution Service
Extends the base code execution service with real-time WebSocket notifications
"""

import asyncio
import logging
from typing import Optional
from datetime import datetime

from app.services.code_execution import CodeExecutionService
from app.services.message_router import message_router
from app.models.schemas import ExecutionRequest, ExecutionResult

logger = logging.getLogger(__name__)


class WebSocketCodeExecutionService(CodeExecutionService):
    """Code execution service with WebSocket notifications"""
    
    def __init__(self, skip_docker_init=False):
        super().__init__(skip_docker_init)
        self.message_router = message_router
    
    async def execute_code_with_notifications(
        self, 
        request: ExecutionRequest,
        notify_hooks: bool = True
    ) -> ExecutionResult:
        """
        Execute code with real-time WebSocket notifications
        
        Args:
            request: Code execution request
            notify_hooks: Whether to trigger hook notifications
            
        Returns:
            ExecutionResult: The execution result
        """
        session_id = request.session_id
        execution_id = f"exec_{datetime.utcnow().timestamp()}"
        
        try:
            # Notify execution start
            await self.message_router.notify_execution_start(
                session_id=session_id,
                language=request.language,
                code_preview=request.code[:100],
                execution_id=execution_id
            )
            
            # Execute the code
            result = await self.execute_code(request, trigger_hooks=False)
            
            # Notify execution complete
            await self.message_router.notify_execution_complete(
                session_id=session_id,
                result=result,
                execution_id=execution_id
            )
            
            return result
            
        except Exception as e:
            logger.error(f"WebSocket code execution error: {e}", exc_info=True)
            
            # Create error result
            error_result = ExecutionResult(
                stdout="",
                stderr=f"Execution service error: {str(e)}",
                exit_code=1,
                execution_time=0.0
            )
            
            # Notify error
            await self.message_router.notify_execution_complete(
                session_id=session_id,
                result=error_result,
                execution_id=execution_id
            )
            
            return error_result
    
    async def stream_execution_output(
        self, 
        session_id: str, 
        output_lines: list, 
        execution_id: Optional[str] = None
    ):
        """
        Stream execution output line by line to WebSocket clients
        
        Args:
            session_id: Target session ID
            output_lines: List of output lines
            execution_id: Optional execution identifier
        """
        for line in output_lines:
            if line.strip():  # Only send non-empty lines
                await self.message_router.stream_execution_output(
                    session_id=session_id,
                    output=line,
                    stream="stdout",
                    execution_id=execution_id
                )
                # Small delay to simulate real-time streaming
                await asyncio.sleep(0.1)


# Global WebSocket-enabled code execution service
websocket_code_execution_service = WebSocketCodeExecutionService()