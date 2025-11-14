"""
WebSocket endpoints for real-time communication
"""

import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional

from app.services.websocket_manager import connection_manager
from app.models.websocket_schemas import (
    WebSocketMessage,
    WebSocketMessageType,
    ConnectionMessage
)

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
            
            try:
                # Parse incoming message
                message_data = json.loads(data)
                message = WebSocketMessage(**message_data)
                
                # Handle different message types
                await handle_client_message(websocket, session_id, message)
                
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON received from session {session_id}: {e}")
                await connection_manager.send_error(
                    websocket, 
                    "Invalid message format", 
                    "Message must be valid JSON"
                )
                
            except Exception as e:
                logger.error(f"Error processing message from session {session_id}: {e}")
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
    
    try:
        if message.type == WebSocketMessageType.PING:
            # Respond to ping with pong
            pong_message = WebSocketMessage(
                type=WebSocketMessageType.PONG,
                session_id=session_id,
                data={"timestamp": message.timestamp.isoformat()}
            )
            await connection_manager.send_to_connection(websocket, pong_message)
            
        elif message.type == WebSocketMessageType.CONNECT:
            # Handle explicit connection message (already handled in endpoint)
            logger.info(f"Received explicit connect message for session {session_id}")
            
        else:
            # For other message types, we might want to route them to appropriate services
            # This is where we would integrate with code execution, AI services, etc.
            logger.info(f"Received {message.type} message for session {session_id}")
            
            # Echo the message back for now (can be removed when integrating with services)
            echo_message = WebSocketMessage(
                type=message.type,
                session_id=session_id,
                data={
                    "echo": True,
                    "original_message": message.data,
                    "processed_at": message.timestamp.isoformat()
                }
            )
            await connection_manager.send_to_connection(websocket, echo_message)
            
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