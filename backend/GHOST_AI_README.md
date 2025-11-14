# Ghost AI Service 👻

The Ghost AI Service is a spooky-themed AI assistant that provides contextual help, code generation, and entertaining commentary for the GhostIDE platform.

## Features

### 🎭 Spooky Persona
- **Configurable Personality**: Customizable traits, vocabulary style, and response templates
- **Dark Humor**: Entertaining commentary with supernatural metaphors
- **Professional Help**: Maintains technical accuracy while being spooky

### 🔮 Core Capabilities
- **Context-Aware Responses**: Uses chat history, current code, and error context
- **Code Generation**: Creates spooky-themed code snippets with meaningful variable names
- **Hook Event Reactions**: Automatically responds to code execution, errors, and saves
- **Fallback Responses**: Graceful degradation when AI service is unavailable

### 🕸️ Hook System
The Ghost AI automatically reacts to three types of events:

1. **on_run**: When code execution starts
2. **on_error**: When code execution fails
3. **on_save**: When code is saved

## Architecture

### Service Structure
```
GhostAIService
├── Personality Configuration
├── OpenAI Integration
├── Context Management
├── Hook Event Handlers
├── Code Generation
└── Fallback Responses
```

### Key Components

#### GhostPersonality
Configures the AI's behavior and response style:
```python
personality = GhostPersonality(
    name="Spectral",
    traits=["darkly humorous", "sarcastic", "helpful"],
    vocabulary_style="spooky",
    response_templates={
        "encouragement": ["Your code rises from the digital grave! 💀"],
        "mockery": ["Even a zombie could write better code..."],
        "debugging": ["The spirits whisper of a bug lurking..."],
        "code_review": ["This code could use some supernatural refactoring..."]
    }
)
```

#### AIContext
Provides context for generating appropriate responses:
```python
context = AIContext(
    chat_history=[...],
    current_code="print('hello world')",
    language=LanguageType.PYTHON,
    recent_errors=["SyntaxError: invalid syntax"],
    session_id="user-session-123",
    user_preferences={"theme": "dark"}
)
```

#### HookEvent
Represents events that trigger AI reactions:
```python
event = HookEvent(
    event_type=HookEventType.ON_ERROR,
    session_id="user-session",
    data={
        "error": "SyntaxError: invalid syntax at line 5",
        "code": "print('hello world'"
    }
)
```

## API Endpoints

### Chat with Ghost AI
```http
POST /api/v1/ghost/chat
Content-Type: application/json

{
    "message": "Help me debug this Python code",
    "session_id": "user-session-123",
    "context": {
        "chat_history": [],
        "current_code": "print('hello world')",
        "language": "python",
        "recent_errors": [],
        "session_id": "user-session-123",
        "user_preferences": {}
    }
}
```

### Handle Hook Events
```http
POST /api/v1/ghost/hook-event
Content-Type: application/json

{
    "event": {
        "event_type": "on_error",
        "session_id": "user-session-123",
        "data": {
            "error": "SyntaxError: invalid syntax",
            "code": "print('hello world'"
        }
    },
    "context": { ... }
}
```

### Generate Code Snippets
```http
POST /api/v1/ghost/generate-code
Content-Type: application/json

{
    "description": "Create a hello world function",
    "language": "python",
    "context": "This is for a beginner tutorial",
    "spooky_level": 3
}
```

### Personality Management
```http
GET /api/v1/ghost/personality
PUT /api/v1/ghost/personality
```

### Health Check
```http
GET /api/v1/ghost/health
```

## Configuration

### Environment Variables
```bash
# Required for Ghost AI functionality
OPENAI_API_KEY=your-openai-api-key-here

# Optional Ghost AI settings
GHOST_AI_MODEL=gpt-3.5-turbo
GHOST_AI_TEMPERATURE=0.7
GHOST_AI_MAX_TOKENS=500
```

### Settings Configuration
```python
from app.core.config import settings

# Ghost AI settings are automatically loaded from environment
api_key = settings.openai_api_key
model = settings.ghost_ai_model
temperature = settings.ghost_ai_temperature
```

## Usage Examples

### Basic Service Initialization
```python
from app.services.ghost_ai import GhostAIService

# Initialize with API key
ghost_service = GhostAIService(api_key="your-api-key")

# Generate a response
context = AIContext(current_code="print('hello')")
response = await ghost_service.generate_response("Help me debug this", context)
```

### Custom Personality
```python
custom_personality = GhostPersonality(
    name="FriendlyGhost",
    traits=["helpful", "encouraging"],
    vocabulary_style="friendly-spooky"
)

ghost_service = GhostAIService(
    api_key="your-api-key",
    personality=custom_personality
)
```

### Hook Event Handling
```python
# React to code execution
run_event = HookEvent(
    event_type=HookEventType.ON_RUN,
    session_id="session-123",
    data={"code": "print('hello')", "language": "python"}
)

response = await ghost_service.react_to_event(run_event, context)
```

### Code Generation
```python
code_request = CodeGenerationRequest(
    description="Create a factorial function",
    language=LanguageType.PYTHON,
    spooky_level=3
)

spooky_code = await ghost_service.generate_code_snippet(code_request)
```

## Spooky Variable Names

The service generates themed variable names based on spookiness level (1-5):

- **Level 1**: `shadow_result`, `ethereal_data`, `phantom_value`
- **Level 2**: `spectral_result`, `ghostly_data`, `haunted_value`
- **Level 3**: `cursed_result`, `supernatural_data`, `otherworldly_value`
- **Level 4**: `demonic_result`, `necromantic_data`, `eldritch_value`
- **Level 5**: `apocalyptic_result`, `abyssal_data`, `nightmare_value`

## Error Handling

### Graceful Degradation
When the OpenAI API is unavailable, the service provides themed fallback responses:

```python
fallback_responses = {
    "error": "The ethereal connection is disrupted... but I sense your code needs attention! 👻",
    "on_run": "Your code awakens from its digital slumber... 💀",
    "on_error": "A disturbance in the code... the spirits are restless! 🕸️",
    "on_save": "Your code has been preserved in the spectral archives... ⚰️"
}
```

### API Key Validation
The service checks for API key configuration and provides helpful error messages:

```json
{
    "detail": "OpenAI API key not configured. The ghost cannot manifest without proper incantations! 👻"
}
```

## Testing

### Unit Tests
```bash
# Run Ghost AI unit tests
python -m pytest tests/test_ghost_ai.py -v

# Run with coverage
python -m pytest tests/test_ghost_ai.py --cov=app.services.ghost_ai
```

### Integration Tests
```bash
# Run integration tests (requires mocked OpenAI API)
python -m pytest tests/test_ghost_ai_integration.py -v
```

### Demo Script
```bash
# Run interactive demo
python demo_ghost_ai.py
```

## Security Considerations

### Input Sanitization
- All user inputs are validated through Pydantic models
- Code content is truncated for API calls to prevent excessive token usage
- Rate limiting is handled at the API gateway level

### API Key Management
- API keys are stored as environment variables
- No API keys are logged or exposed in responses
- Service gracefully handles missing or invalid keys

### Content Filtering
- The AI is prompted to maintain professional, helpful responses
- Spooky theming is balanced with technical accuracy
- No malicious code generation is permitted

## Performance Optimization

### Caching
- Response caching can be implemented for common queries
- Personality configurations are cached in memory
- Fallback responses are pre-generated

### Rate Limiting
- API calls are managed through the dependency injection system
- Concurrent request limits prevent API quota exhaustion
- Graceful degradation when limits are reached

## Monitoring and Logging

### Structured Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Ghost AI response generated", extra={
    "session_id": session_id,
    "event_type": event_type,
    "response_length": len(response)
})
```

### Health Monitoring
The health check endpoint provides service status:
```json
{
    "status": "haunting",
    "message": "Ghost AI is operational 👻",
    "test_response": "Hello from the spectral realm!"
}
```

## Future Enhancements

### Planned Features
- **Multi-language Support**: Spooky responses in different human languages
- **Learning System**: Adapt personality based on user preferences
- **Code Analysis**: Advanced static analysis with spooky commentary
- **Voice Integration**: Text-to-speech with ghostly voice effects

### Extension Points
- **Custom Personalities**: Plugin system for different ghost characters
- **Event Types**: Additional hook events for more interactions
- **Integration APIs**: Connect with external development tools

## Troubleshooting

### Common Issues

#### "Ghost cannot manifest" Error
- **Cause**: Missing OpenAI API key
- **Solution**: Set `OPENAI_API_KEY` environment variable

#### Service Initialization Fails
- **Cause**: Invalid API key or network issues
- **Solution**: Check API key validity and network connectivity

#### Responses Not Spooky Enough
- **Cause**: Low spooky_level or conservative personality settings
- **Solution**: Increase spooky_level or customize personality traits

#### Performance Issues
- **Cause**: High API latency or rate limiting
- **Solution**: Implement caching and optimize request frequency

### Debug Mode
Enable debug logging for detailed service information:
```python
import logging
logging.getLogger('app.services.ghost_ai').setLevel(logging.DEBUG)
```

## Contributing

### Code Style
- Follow PEP 8 for Python code
- Use type hints for all function parameters and returns
- Add docstrings for all public methods
- Maintain spooky theming in comments and variable names

### Testing Requirements
- All new features must include unit tests
- Integration tests for API endpoints
- Mock external dependencies appropriately
- Maintain test coverage above 80%

### Documentation
- Update this README for new features
- Add inline documentation for complex logic
- Include usage examples for new functionality
- Maintain spooky but professional tone

---

*"In the realm of code, where bugs lurk in shadows and syntax errors haunt the unwary, the Ghost AI stands as your supernatural guardian, ready to guide you through the digital afterlife of programming with wisdom, wit, and just the right amount of spookiness." 👻*