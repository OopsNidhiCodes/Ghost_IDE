"""
WebSocket endpoints for real-time communication
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional

from app.services.websocket_manager import connection_manager
from app.services.websocket_code_execution import websocket_code_execution_service
from app.services.ghost_ai import get_ghost_ai_service, AIContext
from app.models.websocket_schemas import (
    WebSocketMessage,
    WebSocketMessageType,
    ConnectionMessage
)
from app.models.schemas import ExecutionRequest

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str,
    token: Optional[str] = Query(None)
):
    """
    Main WebSocket endpoint for real-time communication
    
    Args:
        websocket: WebSocket connection
        session_id: User session ID
        token: Optional authentication token (for future use)
    """
    logger.info(f"WebSocket connection attempt for session: {session_id}")
    
    # Connect to the session
    connected = await connection_manager.connect(websocket, session_id)
    if not connected:
        logger.error(f"Failed to establish WebSocket connection for session: {session_id}")
        return
    
    try:
        while True:
            # Wait for messages from client
            data = await websocket.receive_text()
            logger.debug(f"Received raw message from session {session_id}: {data[:200]}")
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                logger.debug(f"Parsed message data: type={message_data.get('type')}, has_data={bool(message_data.get('data'))}")
                message = WebSocketMessage(**message_data)
                logger.info(f"Processing message type '{message.type}' for session {session_id}")
                
                # Handle different message types
                await handle_client_message(websocket, session_id, message)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received from session {session_id}: {e}\nData: {data[:500]}")
                await connection_manager.send_error(
                    websocket, 
                    "Invalid message format", 
                    "Message must be valid JSON"
                )
                
            except Exception as e:
                logger.error(f"Error processing message from session {session_id}: {e}\nData: {data[:500]}", exc_info=True)
                await connection_manager.send_error(
                    websocket,
                    "Message processing error",
                    str(e)
                )
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session: {session_id}")
        
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {e}")
        
    finally:
        # Clean up connection
        await connection_manager.disconnect(websocket)


async def handle_client_message(websocket: WebSocket, session_id: str, message: WebSocketMessage):
    """
    Handle incoming messages from clients
    
    Args:
        websocket: The WebSocket connection
        session_id: The session ID
        message: The received message
    """
    logger.debug(f"Handling message type {message.type} for session {session_id}")
    
    # Get the enum value as a string
    msg_type = message.type.value if isinstance(message.type, WebSocketMessageType) else str(message.type)
    
    try:
        if msg_type == "ping" or message.type == WebSocketMessageType.PING:
            # Respond to ping with pong
            pong_message = WebSocketMessage(
                type=WebSocketMessageType.PONG,
                session_id=session_id,
                data={"timestamp": message.timestamp.isoformat()}
            )
            await connection_manager.send_to_connection(websocket, pong_message)
            
        elif msg_type == "connect" or message.type == WebSocketMessageType.CONNECT:
            # Handle explicit connection message (already handled in endpoint)
            logger.info(f"Received explicit connect message for session {session_id}")
            
        elif msg_type == "execute_code" or message.type == WebSocketMessageType.EXECUTE_CODE:
            # Handle code execution
            logger.info(f"Executing code for session {session_id}")
            try:
                # Extract execution request data
                code = message.data.get("code", "")
                language = message.data.get("language", "python")
                user_input = message.data.get("input", "")
                
                # Create execution request
                execution_request = ExecutionRequest(
                    code=code,
                    language=language,
                    input=user_input,
                    session_id=session_id
                )
                
                # Execute code with WebSocket notifications
                result = await websocket_code_execution_service.execute_code_with_notifications(
                    execution_request
                )
                
                logger.info(f"Code execution completed for session {session_id}")
                
            except Exception as e:
                logger.error(f"Code execution error for session {session_id}: {e}")
                await connection_manager.send_error(
                    websocket,
                    "Code execution failed",
                    str(e)
                )
        
        elif msg_type == "ghost_chat" or message.type == WebSocketMessageType.GHOST_CHAT:
            # Handle Ghost AI chat
            logger.info(f"Processing Ghost AI message for session {session_id}")
            try:
                user_message = message.data.get("message", "")
                context_data = message.data.get("context", {})
                
                # Convert dict to AIContext object
                ai_context = AIContext(
                    chat_history=context_data.get("chat_history", []),
                    current_code=context_data.get("current_code", ""),
                    language=context_data.get("language", "python"),
                    recent_errors=context_data.get("recent_errors", []),
                    session_id=session_id,
                    user_preferences=context_data.get("user_preferences", {})
                )
                
                # Get AI response
                ghost_service = get_ghost_ai_service()
                ai_response = await ghost_service.generate_response(
                    user_message,
                    ai_context
                )
                
                # Send AI response
                response_msg = WebSocketMessage(
                    type=WebSocketMessageType.GHOST_RESPONSE,
                    session_id=session_id,
                    data={
                        "message": ai_response,
                        "context": context_data
                    }
                )
                await connection_manager.send_to_connection(websocket, response_msg)
                
                logger.info(f"Ghost AI response sent for session {session_id}")
                
            except Exception as e:
                logger.error(f"Ghost AI error for session {session_id}: {e}")
                await connection_manager.send_error(
                    websocket,
                    "Ghost AI error",
                    str(e)
                )
        
        elif msg_type == "save_file" or message.type == WebSocketMessageType.SAVE_FILE:
            # Handle file save
            logger.info(f"Saving file for session {session_id}")
            # File save logic would go here
            confirm_msg = WebSocketMessage(
                type=WebSocketMessageType.FILE_SAVED,
                session_id=session_id,
                data=message.data
            )
            await connection_manager.send_to_connection(websocket, confirm_msg)
            
        elif msg_type == "hook_event":
            # Handle hook events
            logger.info(f"Received hook event for session {session_id}: {message.data.get('type')}")
            # Hook event handling would go here
            
        else:
            # Unknown message type
            logger.warning(f"Unknown message type {msg_type} for session {session_id}")
            
    except Exception as e:
        logger.error(f"Error handling message type {message.type}: {e}")
        await connection_manager.send_error(
            websocket,
            f"Error handling {message.type} message",
            str(e)
        )


@router.get("/ws/status")
async def websocket_status():
    """
    Get WebSocket connection status
    
    Returns:
        dict: Connection statistics
    """
    return {
        "total_connections": connection_manager.get_total_connections(),
        "active_sessions": connection_manager.get_active_sessions(),
        "session_count": len(connection_manager.get_active_sessions())
    }


@router.get("/ws/sessions/{session_id}/connections")
async def get_session_connections(session_id: str):
    """
    Get connection count for a specific session
    
    Args:
        session_id: The session ID
        
    Returns:
        dict: Session connection information
    """
    connection_count = connection_manager.get_session_connection_count(session_id)
    return {
        "session_id": session_id,
        "connection_count": connection_count,
        "is_active": connection_count > 0
    }