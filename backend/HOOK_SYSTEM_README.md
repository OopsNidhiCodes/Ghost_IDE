# GhostIDE Hook System 👻

The Hook System provides automated AI responses to code execution events, creating an interactive and engaging development experience with the Ghost AI assistant.

## Overview

The hook system automatically triggers Ghost AI responses when specific events occur during coding:

- **on_run**: Triggered when code execution starts
- **on_error**: Triggered when code execution fails  
- **on_save**: Triggered when code files are saved

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Code Execution │───▶│   Hook Manager   │───▶│   Ghost AI      │
│     Service     │    │                  │    │    Service      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
┌─────────────────┐             │                        │
│ Session Manager │─────────────┘                        │
│  (File Saves)   │                                      │
└─────────────────┘                                      │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   WebSocket     │◀───│  AI Response     │◀───│  Spooky Response│
│    Manager      │    │   Distribution   │    │   Generation    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components

### HookManagerService

The central service that coordinates hook events and AI responses.

**Key Features:**
- Event-driven architecture
- Execution tracking and statistics
- Enable/disable individual hooks
- Custom event listeners
- Error handling and fallback responses

**Usage:**
```python
from app.services.hook_manager import HookManagerService
from app.services.ghost_ai import GhostAIService

# Initialize
ghost_ai = GhostAIService(api_key="your-key")
hook_manager = HookManagerService(ghost_ai)

# Trigger hooks
await hook_manager.on_run_hook(session_id, code, language)
await hook_manager.on_error_hook(session_id, code, language, error)
await hook_manager.on_save_hook(session_id, code, language, filename)
```

### Hook Events

Each hook event contains:
- `event_type`: Type of hook (on_run, on_error, on_save)
- `session_id`: User session identifier
- `timestamp`: When the event occurred
- `data`: Event-specific data (code, error, filename, etc.)

### AI Context

The AI receives contextual information:
- Chat history (last 10 messages)
- Current code being executed/saved
- Programming language
- Recent errors
- Session preferences

## Integration Points

### Code Execution Service

Automatically triggers hooks during code execution:

```python
# on_run hook triggered when execution starts
result = await code_execution_service.execute_code(request)

# on_error hook triggered if execution fails
if result.exit_code != 0:
    # Hook automatically triggered with error details
```

### Session Management

Triggers on_save hooks when files are updated:

```python
# PUT /api/v1/sessions/{session_id}/files/{file_id}
# POST /api/v1/sessions/{session_id}/files/{file_id}/save
# Both endpoints automatically trigger on_save hooks
```

### WebSocket Communication

AI responses are sent to users via WebSocket:

```json
{
  "type": "ghost_response",
  "session_id": "session-123",
  "data": {
    "response": "Your code rises from the digital grave! 💀",
    "hook_type": "on_run",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## API Endpoints

### Hook Status
```http
GET /api/v1/hooks/status
```
Returns hook system statistics and enabled status.

### Hook Execution History
```http
GET /api/v1/hooks/executions?session_id=xxx&event_type=on_run&limit=100
```
Returns recent hook executions with filtering options.

### Enable/Disable Hooks
```http
POST /api/v1/hooks/enable/on_run
POST /api/v1/hooks/disable/on_error
```
Enable or disable specific hook types.

### Test Hooks
```http
POST /api/v1/hooks/test/on_run?session_id=xxx&code=print('test')
```
Manually trigger hooks for testing purposes.

## Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your-openai-api-key
```

### Hook Settings

Hooks can be enabled/disabled at runtime:

```python
hook_manager.enable_hook(HookEventType.ON_RUN)
hook_manager.disable_hook(HookEventType.ON_ERROR)
```

## Monitoring and Debugging

### Statistics

The hook system tracks:
- Total events processed
- Success/failure rates
- Events by type
- Execution times
- Error details

### Execution History

All hook executions are logged with:
- Event details
- AI response
- Execution status
- Timing information
- Error messages (if any)

### Logging

Hook events are logged at appropriate levels:
```python
logger.info(f"Hook {event_type} completed successfully")
logger.error(f"Hook {event_type} failed: {error}")
logger.warning(f"Failed to trigger hook: {error}")
```

## Error Handling

### Graceful Degradation

- If AI service fails, fallback responses are used
- Hook failures don't break core functionality
- WebSocket errors are handled gracefully

### Fallback Responses

When AI service is unavailable:
```python
fallbacks = {
    "on_run": "Your code awakens from its digital slumber... 💀",
    "on_error": "A disturbance in the code... the spirits are restless! 🕸️",
    "on_save": "Your code has been preserved in the spectral archives... ⚰️"
}
```

## Testing

### Unit Tests

```bash
pytest tests/test_hook_integration.py -v
```

### Integration Tests

The test suite covers:
- Hook manager functionality
- AI service integration
- WebSocket communication
- Error handling
- Statistics tracking

### Manual Testing

Use the demo script:
```bash
python demo_hook_system.py
```

## Performance Considerations

### Async Operations

All hook operations are asynchronous to avoid blocking:
```python
async def trigger_hook(self, event_type, session_id, data):
    # Non-blocking AI response generation
    response = await self.ghost_ai.react_to_event(event, context)
```

### Rate Limiting

Consider implementing rate limiting for:
- AI API calls
- Hook executions per session
- WebSocket message frequency

### Caching

AI responses can be cached for:
- Common error patterns
- Repeated code snippets
- Session-specific context

## Security

### Input Validation

All hook data is validated:
- Code content sanitization
- Session ID validation
- Language type verification

### API Security

Hook management endpoints should be:
- Authenticated
- Rate limited
- Logged for audit

## Future Enhancements

### Planned Features

1. **Custom Hook Types**: User-defined hook events
2. **Hook Chaining**: Sequential hook execution
3. **Conditional Hooks**: Rules-based hook triggering
4. **Hook Analytics**: Advanced metrics and insights
5. **Hook Templates**: Pre-configured hook responses

### Integration Opportunities

1. **Code Quality Hooks**: Trigger on code analysis results
2. **Collaboration Hooks**: Multi-user session events
3. **Learning Hooks**: Educational content delivery
4. **Performance Hooks**: Code optimization suggestions

## Troubleshooting

### Common Issues

1. **AI Service Unavailable**
   - Check API key configuration
   - Verify network connectivity
   - Review rate limits

2. **Hooks Not Triggering**
   - Verify hook is enabled
   - Check session ID validity
   - Review error logs

3. **WebSocket Issues**
   - Confirm connection status
   - Check session management
   - Verify message routing

### Debug Commands

```python
# Check hook status
hook_manager.get_hook_statistics()

# View recent executions
hook_manager.get_hook_executions(limit=10)

# Test specific hook
await hook_manager.on_run_hook("test-session", "print('test')", "python")
```

---

*The spirits approve of this hook system! May your code be forever haunted by helpful AI responses! 👻*