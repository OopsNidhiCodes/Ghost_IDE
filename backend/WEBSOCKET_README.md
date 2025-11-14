# WebSocket Communication System

This document describes the WebSocket communication system implemented for GhostIDE, providing real-time interactions between the backend and frontend.

## Overview

The WebSocket system enables real-time communication for:
- Code execution updates and streaming output
- Ghost AI responses and typing indicators
- Hook event notifications
- Session updates and file save notifications
- Connection management and error handling

## Architecture

### Core Components

1. **WebSocket Schemas** (`app/models/websocket_schemas.py`)
   - Defines message types and data structures
   - Provides type safety for WebSocket communications

2. **Connection Manager** (`app/services/websocket_manager.py`)
   - Manages WebSocket connections per session
   - Handles connection/disconnection events
   - Routes messages to appropriate clients

3. **Message Router** (`app/services/message_router.py`)
   - High-level interface for sending notifications
   - Used by other services to send WebSocket messages
   - Provides typed methods for different message types

4. **WebSocket Endpoints** (`app/api/endpoints/websocket.py`)
   - FastAPI WebSocket endpoints
   - Handles client connections and message processing

## Usage

### Connecting to WebSocket

Connect to the WebSocket endpoint with a session ID:

```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);

ws.onopen = function(event) {
    console.log('Connected to WebSocket');
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    handleWebSocketMessage(message);
};
```

### Message Types

#### Connection Messages
- `connect`: Connection established
- `disconnect`: Connection closed
- `ping`/`pong`: Keep-alive messages

#### Code Execution Messages
- `execution_start`: Code execution began
- `execution_output`: Streaming output from code execution
- `execution_complete`: Code execution finished
- `execution_error`: Code execution failed

#### Ghost AI Messages
- `ai_response`: AI response message
- `ai_typing`: AI typing indicator
- `ai_error`: AI error message

#### Hook Messages
- `hook_triggered`: Hook event occurred (on_run, on_error, on_save)

#### Session Messages
- `session_update`: Session data changed
- `file_saved`: File was saved

#### Error Messages
- `error`: General error notification

### Message Structure

All WebSocket messages follow this structure:

```json
{
    "type": "message_type",
    "timestamp": "2023-10-01T12:00:00Z",
    "session_id": "session_123",
    "data": {
        // Message-specific data
    }
}
```

### Using the Message Router

Services can send WebSocket notifications using the message router:

```python
from app.services.message_router import message_router

# Notify execution start
await message_router.notify_execution_start(
    session_id="session_123",
    language="python",
    code_preview="print('hello')"
)

# Stream execution output
await message_router.stream_execution_output(
    session_id="session_123",
    output="Hello, World!",
    stream="stdout"
)

# Send AI response
await message_router.send_ai_response(
    session_id="session_123",
    message=chat_message
)
```

## Integration Examples

### Code Execution with WebSocket

Use the WebSocket-enabled execution endpoint:

```python
# POST /api/v1/execution/execute/websocket
{
    "code": "print('Hello, World!')",
    "language": "python",
    "session_id": "session_123",
    "timeout": 30
}
```

This will send WebSocket notifications for:
1. Execution start
2. Hook triggered (on_run)
3. Execution complete
4. Hook triggered (on_error) if execution fails

### Ghost AI Integration

The Ghost AI service can send real-time updates:

```python
# Set typing indicator
await message_router.set_ai_typing(session_id, True)

# Send AI response
await message_router.send_ai_response(session_id, chat_message)

# Clear typing indicator
await message_router.set_ai_typing(session_id, False)
```

## Connection Management

### Connection Statistics

Get WebSocket connection statistics:

```bash
GET /ws/status
```

Response:
```json
{
    "total_connections": 5,
    "active_sessions": ["session_1", "session_2"],
    "session_count": 2
}
```

### Session Connections

Get connections for a specific session:

```bash
GET /ws/sessions/{session_id}/connections
```

Response:
```json
{
    "session_id": "session_123",
    "connection_count": 2,
    "is_active": true
}
```

## Error Handling

The WebSocket system includes comprehensive error handling:

1. **Connection Errors**: Automatic cleanup of failed connections
2. **Message Validation**: Invalid messages return error responses
3. **Service Errors**: Errors in services are propagated via WebSocket
4. **Reconnection**: Clients can reconnect with the same session ID

## Testing

The WebSocket system includes comprehensive tests:

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test WebSocket communication end-to-end
- **Connection Tests**: Test connection management and cleanup

Run WebSocket tests:

```bash
python -m pytest tests/test_websocket.py tests/test_websocket_integration.py -v
```

## Security Considerations

1. **Session Validation**: WebSocket connections are tied to session IDs
2. **Message Validation**: All messages are validated using Pydantic schemas
3. **Resource Limits**: Connection limits and message size restrictions
4. **Error Isolation**: Errors in one connection don't affect others

## Performance

The WebSocket system is designed for performance:

- **Efficient Routing**: Messages are only sent to relevant connections
- **Connection Pooling**: Multiple connections per session are supported
- **Async Processing**: All operations are asynchronous
- **Memory Management**: Automatic cleanup of disconnected clients

## Future Enhancements

Potential improvements for the WebSocket system:

1. **Authentication**: Add token-based authentication for WebSocket connections
2. **Rate Limiting**: Implement rate limiting for message sending
3. **Message Persistence**: Store messages for offline clients
4. **Clustering**: Support for multiple backend instances
5. **Compression**: Enable WebSocket message compression