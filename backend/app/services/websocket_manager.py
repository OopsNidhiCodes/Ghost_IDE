"""
WebSocket connection manager for handling multiple client connections
"""

import json
import logging
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from app.models.websocket_schemas import (
    WebSocketMessage, 
    WebSocketMessageType,
    WebSocketMessageUnion,
    ErrorMessage
)

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time communication"""
    
    def __init__(self):
        # Active connections: session_id -> list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Connection metadata: websocket -> session_id
        self.connection_sessions: Dict[WebSocket, str] = {}
        # Session subscribers: session_id -> set of connection IDs
        self.session_subscribers: Dict[str, Set[str]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str) -> bool:
        """
        Accept a new WebSocket connection and associate it with a session
        
        Args:
            websocket: The WebSocket connection
            session_id: The session ID to associate with this connection
            
        Returns:
            bool: True if connection was successful
        """
        try:
            await websocket.accept()
            
            # Initialize session connections list if needed
            if session_id not in self.active_connections:
                self.active_connections[session_id] = []
                self.session_subscribers[session_id] = set()
            
            # Add connection to session
            self.active_connections[session_id].append(websocket)
            self.connection_sessions[websocket] = session_id
            
            # Generate unique connection ID
            connection_id = f"{session_id}_{len(self.active_connections[session_id])}"
            self.session_subscribers[session_id].add(connection_id)
            
            logger.info(f"WebSocket connected for session {session_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect WebSocket for session {session_id}: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection
        
        Args:
            websocket: The WebSocket connection to remove
        """
        try:
            session_id = self.connection_sessions.get(websocket)
            if session_id:
                # Remove from active connections
                if session_id in self.active_connections:
                    if websocket in self.active_connections[session_id]:
                        self.active_connections[session_id].remove(websocket)
                    
                    # Clean up empty session
                    if not self.active_connections[session_id]:
                        del self.active_connections[session_id]
                        if session_id in self.session_subscribers:
                            del self.session_subscribers[session_id]
                
                # Remove connection metadata
                del self.connection_sessions[websocket]
                
                logger.info(f"WebSocket disconnected for session {session_id}")
            
        except Exception as e:
            logger.error(f"Error during WebSocket disconnect: {e}")
    
    async def send_to_connection(self, websocket: WebSocket, message: WebSocketMessageUnion):
        """
        Send a message to a specific WebSocket connection
        
        Args:
            websocket: The target WebSocket connection
            message: The message to send
        """
        try:
            message_dict = message.model_dump()
            await websocket.send_text(json.dumps(message_dict, default=str))
            
        except Exception as e:
            logger.error(f"Failed to send message to WebSocket: {e}")
            # Connection might be closed, remove it
            await self.disconnect(websocket)
    
    async def send_to_session(self, session_id: str, message: WebSocketMessageUnion):
        """
        Send a message to all connections in a session
        
        Args:
            session_id: The target session ID
            message: The message to send
        """
        if session_id not in self.active_connections:
            logger.warning(f"No active connections for session {session_id}")
            return
        
        # Set session_id in message if not already set
        if not message.session_id:
            message.session_id = session_id
        
        # Send to all connections in the session
        connections_to_remove = []
        for websocket in self.active_connections[session_id]:
            try:
                await self.send_to_connection(websocket, message)
            except Exception as e:
                logger.error(f"Failed to send to connection in session {session_id}: {e}")
                connections_to_remove.append(websocket)
        
        # Clean up failed connections
        for websocket in connections_to_remove:
            await self.disconnect(websocket)
    
    async def broadcast_to_all(self, message: WebSocketMessageUnion):
        """
        Broadcast a message to all active connections
        
        Args:
            message: The message to broadcast
        """
        for session_id in list(self.active_connections.keys()):
            await self.send_to_session(session_id, message)
    
    async def send_error(self, websocket: WebSocket, error: str, detail: str = "", code: int = 500):
        """
        Send an error message to a specific connection
        
        Args:
            websocket: The target WebSocket connection
            error: Error message
            detail: Additional error details
            code: Error code
        """
        error_message = ErrorMessage(
            data={
                "error": error,
                "detail": detail,
                "code": code
            }
        )
        await self.send_to_connection(websocket, error_message)
    
    async def send_session_error(self, session_id: str, error: str, detail: str = "", code: int = 500):
        """
        Send an error message to all connections in a session
        
        Args:
            session_id: The target session ID
            error: Error message
            detail: Additional error details
            code: Error code
        """
        error_message = ErrorMessage(
            session_id=session_id,
            data={
                "error": error,
                "detail": detail,
                "code": code
            }
        )
        await self.send_to_session(session_id, error_message)
    
    def get_session_connection_count(self, session_id: str) -> int:
        """
        Get the number of active connections for a session
        
        Args:
            session_id: The session ID
            
        Returns:
            int: Number of active connections
        """
        return len(self.active_connections.get(session_id, []))
    
    def get_total_connections(self) -> int:
        """
        Get the total number of active connections
        
        Returns:
            int: Total number of active connections
        """
        return sum(len(connections) for connections in self.active_connections.values())
    
    def get_active_sessions(self) -> List[str]:
        """
        Get list of session IDs with active connections
        
        Returns:
            List[str]: List of active session IDs
        """
        return list(self.active_connections.keys())


# Global connection manager instance
connection_manager = ConnectionManager()