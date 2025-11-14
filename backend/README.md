# GhostIDE Backend API

This is the backend API for GhostIDE, built with FastAPI and PostgreSQL.

## Features Implemented

### Core API Structure
- ✅ FastAPI application with basic routing structure
- ✅ CORS middleware configuration for frontend integration
- ✅ Application lifespan management with database initialization
- ✅ Health check and root endpoints

### Database Integration
- ✅ SQLAlchemy async setup with PostgreSQL support
- ✅ Database connection management and session handling
- ✅ Automatic table creation on startup

### Data Models
- ✅ Pydantic schemas for request/response validation
- ✅ SQLAlchemy database models for persistence
- ✅ Support for UserSession, CodeFile, and ExecutionRequest models
- ✅ Comprehensive validation and type safety

### Session Management API
- ✅ Create new user sessions with preferences
- ✅ Retrieve session data with files and chat history
- ✅ Update session preferences and language settings
- ✅ Delete sessions with cascade cleanup
- ✅ File management within sessions (create, list)

### Testing
- ✅ Unit tests for Pydantic models with validation
- ✅ API endpoint structure tests
- ✅ Basic integration tests
- ✅ 23 passing tests covering core functionality

## API Endpoints

### Health & Status
- `GET /` - Root endpoint with welcome message
- `GET /health` - Health check endpoint

### Session Management
- `POST /api/v1/sessions/` - Create new session
- `GET /api/v1/sessions/{session_id}` - Get session details
- `PUT /api/v1/sessions/{session_id}` - Update session
- `DELETE /api/v1/sessions/{session_id}` - Delete session

### File Management
- `POST /api/v1/sessions/{session_id}/files` - Create file in session
- `GET /api/v1/sessions/{session_id}/files` - List session files

## Data Models

### UserSession
- Session ID and metadata
- Current programming language
- User preferences (theme, font size, auto-save settings)
- Associated files and chat history
- Creation and activity timestamps

### CodeFile
- File ID, name, and content
- Programming language type
- Last modified timestamp
- Session association

### ExecutionRequest
- Code content and language
- Optional input for interactive programs
- Timeout and session configuration

## Database Schema

### Tables
- `user_sessions` - User session data and preferences
- `code_files` - Code files associated with sessions
- `chat_messages` - Chat history with Ghost AI

### Relationships
- Sessions have many files (one-to-many)
- Sessions have many chat messages (one-to-many)
- Cascade delete for cleanup

## Configuration

### Environment Variables
- `DATABASE_URL` - PostgreSQL connection string
- `ECHO_SQL` - Enable SQL query logging (development)

### Dependencies
- FastAPI 0.104.1 - Web framework
- SQLAlchemy 2.0.23 - Database ORM
- Pydantic 2.5.0 - Data validation
- asyncpg 0.30.0 - PostgreSQL async driver
- pytest 7.4.3 - Testing framework

## Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test files
python -m pytest tests/test_models.py -v
python -m pytest tests/test_working.py -v

# Run with coverage
python -m pytest --cov=app tests/
```

## Development Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up PostgreSQL database or use Docker Compose

3. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Access API documentation at `http://localhost:8000/docs`

## Next Steps

The core backend API structure is complete and ready for:
- Code execution service integration (Task 3)
- Ghost AI service implementation (Task 4)
- WebSocket communication setup (Task 5)
- Frontend integration and testing

All database models and API endpoints are in place to support the full GhostIDE feature set as defined in the requirements.