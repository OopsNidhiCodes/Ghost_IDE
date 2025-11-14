# Code Execution Service

This document describes the implementation of Task 3: "Implement code execution service with Docker integration" for the GhostIDE project.

## Overview

The code execution service provides secure, isolated code execution for multiple programming languages using Docker containers. It includes validation, sanitization, resource limits, and asynchronous execution capabilities.

## Components Implemented

### 1. Docker Containers

Created Docker containers for supported languages:
- **Python** (`backend/dockerfiles/python.Dockerfile`)
- **JavaScript** (`backend/dockerfiles/javascript.Dockerfile`) 
- **Java** (`backend/dockerfiles/java.Dockerfile`)
- **C++** (`backend/dockerfiles/cpp.Dockerfile`)

Each container includes:
- Minimal base image for security
- Non-root user execution
- Execution scripts with timeout handling
- Resource limitations

### 2. CodeExecutionService Class

**File**: `backend/app/services/code_execution.py`

**Key Features**:
- Docker container management
- Code validation and sanitization
- Security checks for dangerous imports/functions
- Timeout and resource limit handling
- Support for multiple programming languages
- Graceful error handling

**Main Methods**:
- `execute_code()` - Execute code in Docker container
- `validate_code()` - Validate and sanitize user code
- `get_supported_languages()` - Get list of supported languages
- `get_language_info()` - Get language configuration details

### 3. Celery Tasks

**File**: `backend/app/services/tasks.py`

**Implemented Tasks**:
- `execute_code_async()` - Asynchronous code execution
- `validate_code_async()` - Asynchronous code validation
- `get_supported_languages()` - Get supported languages list

**Features**:
- Task progress tracking
- Error handling and reporting
- JSON serialization for results

### 4. API Endpoints

**File**: `backend/app/api/endpoints/execution.py`

**Endpoints**:
- `POST /api/v1/execution/execute` - Synchronous code execution
- `POST /api/v1/execution/execute/async` - Asynchronous code execution
- `GET /api/v1/execution/task/{task_id}` - Get async task status
- `POST /api/v1/execution/validate` - Validate code
- `GET /api/v1/execution/languages` - Get supported languages
- `GET /api/v1/execution/languages/{language}` - Get language info

### 5. Security Features

**Code Validation**:
- Size limits (max 50KB)
- Dangerous import detection (Python)
- Language-specific requirements validation

**Container Security**:
- Non-root user execution
- Memory limits (128MB)
- CPU limits (50%)
- Network isolation
- Read-only filesystem
- Temporary filesystem with size limits
- 30-second execution timeout

### 6. Testing

**Test Files**:
- `backend/tests/test_code_execution.py` - Service unit tests
- `backend/tests/test_tasks.py` - Celery task tests
- `backend/tests/test_execution_api.py` - API endpoint tests

**Test Coverage**:
- Code validation (empty, too large, dangerous imports)
- Language support verification
- Execution success and failure scenarios
- Timeout handling
- Container error handling
- API request/response validation

## Usage Examples

### Synchronous Execution
```python
from app.services.code_execution import code_execution_service
from app.models.schemas import ExecutionRequest

request = ExecutionRequest(
    code="print('Hello, World!')",
    language="python",
    session_id="user-session-123",
    timeout=30
)

result = await code_execution_service.execute_code(request)
print(f"Output: {result.stdout}")
print(f"Exit Code: {result.exit_code}")
```

### API Usage
```bash
# Execute Python code
curl -X POST "http://localhost:8000/api/v1/execution/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello, World!\")",
    "language": "python",
    "session_id": "test-session",
    "timeout": 30
  }'

# Get supported languages
curl "http://localhost:8000/api/v1/execution/languages"

# Validate code
curl -X POST "http://localhost:8000/api/v1/execution/validate?code=print('hello')&language=python"
```

## Building and Running

### Build Docker Images
```bash
cd backend
python scripts/build_containers.py
```

### Run Tests
```bash
cd backend
python -m pytest tests/test_code_execution.py tests/test_tasks.py tests/test_execution_api.py -v
```

### Start Services
```bash
# Start Redis (required for Celery)
docker run -d -p 6379:6379 redis:alpine

# Start Celery worker
cd backend
celery -A app.services.celery_app worker --loglevel=info

# Start FastAPI server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Requirements Satisfied

This implementation satisfies the following requirements from the task:

✅ **2.1**: Execute code using appropriate compiler/interpreter  
✅ **2.2**: Display execution output and handle success/failure  
✅ **2.4**: Display error messages and handle execution failures  
✅ **2.5**: Implement timeout and security measures  

## Security Considerations

- All code execution happens in isolated Docker containers
- Non-root user execution prevents privilege escalation
- Network isolation prevents external access
- Resource limits prevent resource exhaustion
- Input validation prevents code injection
- Timeout mechanisms prevent infinite loops
- Read-only filesystem prevents file system modifications

## Future Enhancements

- Additional language support (Go, Rust, etc.)
- Enhanced security scanning
- Performance metrics collection
- Code execution caching
- Streaming output for long-running processes
- Custom resource limits per user/session