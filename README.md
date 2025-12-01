# GhostIDE

A spooky online IDE with an AI assistant that provides darkly humorous coding guidance. Supports secure code execution in multiple languages (Python, JavaScript, Java, C++) using Docker containers.

## Features

- 🎃 **Multi-Language Support**: Execute code in Python, JavaScript, Java, and C++
- 🔒 **Secure Execution**: Docker-based sandboxed code execution with resource limits
- 👻 **Ghost AI Assistant**: AI-powered coding help with spooky personality
- 💬 **Real-Time Chat**: WebSocket-based communication for instant feedback
- 🎨 **Monaco Editor**: Professional code editing experience
- 📁 **File Management**: Create, edit, and organize project files
- 🔐 **Session Management**: Persistent user sessions and project state

## Project Structure

```
ghost-ide/
├── frontend/                 # React TypeScript frontend
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/          # Custom React hooks
│   │   ├── services/       # API and WebSocket services
│   │   ├── store/          # Zustand state management
│   │   └── types/          # TypeScript type definitions
│   ├── public/             # Static assets
│   └── package.json        # Frontend dependencies
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models and schemas
│   │   ├── services/       # Business logic (execution, chat, files)
│   │   └── middleware/     # Security and authentication
│   ├── dockerfiles/        # Language-specific Docker containers
│   ├── tests/              # Comprehensive test suite
│   └── requirements.txt    # Python dependencies
└── docker-compose.yml      # Development environment
```

## Prerequisites

- **Docker Desktop**: Required for code execution containers
- **Python 3.12+**: Backend runtime
- **Node.js 18+**: Frontend development
- **PostgreSQL**: Database (can use Docker)
- **Redis**: Caching and task queue (can use Docker)

## Development Setup

### 1. Clone the repository
```bash
git clone https://github.com/OopsNidhiCodes/Ghost_IDE.git
cd Ghost_IDE
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Build Docker containers for code execution
python scripts/build_containers.py

# Start backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 4. Database Setup

```bash
# Using Docker:
docker-compose up -d postgres redis

# Or configure your own PostgreSQL and Redis instances
# Update DATABASE_URL and REDIS_URL in backend/.env
```

## Services

- **Frontend**: http://localhost:5173 (Vite dev server)
- **Backend API**: http://localhost:8000
- **WebSocket**: ws://localhost:8000/ws
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
## Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for build tooling and dev server
- **Monaco Editor** for professional code editing
- **WebSocket** for real-time communication
- **Zustand** for state management
- **Tailwind CSS** with custom spooky theme
- **Axios** for HTTP requests

### Backend
- **Python 3.12** with FastAPI
- **PostgreSQL** with SQLAlchemy ORM
- **Redis** for caching and session management
- **Celery** for async task processing
- **Docker** (subprocess CLI) for code execution isolation
- **Pydantic** for data validation
- **WebSockets** for real-time chat and execution feedback

### Security
- Docker container isolation for code execution
- Input validation and sanitization
- Resource limits (CPU, memory, processes)
- Network isolation in execution containers
- Session-based authentication
- Rate limiting on API endpoints
## Technology Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- Monaco Editor for code editing
- Socket.io for real-time communication
- Zustand for state management
## Development Commands

### Frontend
```bash
npm run dev          # Start Vite dev server (port 5173)
npm run build        # Build for production
npm run preview      # Preview production build
npm run test         # Run tests
npm run lint         # Run ESLint
```

### Backend
```bash
# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
pytest                                    # All tests
pytest tests/test_code_execution.py      # Specific test file
pytest -v                                 # Verbose output

# Build execution containers
python scripts/build_containers.py

# Code quality
black .              # Format code
flake8 .            # Lint code
mypy .              # Type checking
```

### Docker Management

```bash
# Build execution containers
docker build -f backend/dockerfiles/python.Dockerfile -t ghostide-python .
docker build -f backend/dockerfiles/javascript.Dockerfile -t ghostide-javascript .
docker build -f backend/dockerfiles/java.Dockerfile -t ghostide-java .
docker build -f backend/dockerfiles/cpp.Dockerfile -t ghostide-cpp .

# List containers
docker images | grep ghostide

# Test execution
docker run --rm -i ghostide-python python3 -c "print('Hello from Docker!')"
docker run --rm -i ghostide-javascript node -e "console.log('Hello from Docker!')"
docker run --rm -i ghostide-java sh -c "echo 'public class Main{public static void main(String[]a){System.out.println(\"Hello!\");}}' > Main.java && javac Main.java && java Main"
docker run --rm -i ghostide-cpp sh -c "echo '#include<iostream>\nint main(){std::cout<<\"Hello!\";return 0;}' > main.cpp && g++ -o main main.cpp && ./main"

# Cleanup
docker system prune -a              # Remove unused containers/images
```

## Project Documentation

- **Backend Services**: See `backend/README.md`
- **Code Execution**: See `backend/CODE_EXECUTION_README.md`
- **Ghost AI**: See `backend/GHOST_AI_README.md`
- **WebSocket API**: See `backend/WEBSOCKET_README.md`
- **Hook System**: See `backend/HOOK_SYSTEM_README.md`
- **Security**: See `backend/SECURITY_README.md`

## Testing

```bash
# Backend tests
cd backend
pytest -v                                  # All tests with verbose output
pytest tests/test_integration.py          # Integration tests
pytest tests/test_code_execution.py       # Code execution tests
pytest --cov=app tests/                   # With coverage report

# Frontend tests
cd frontend
npm run test                               # Run all tests
npm run test:watch                         # Watch mode
```

## Deployment

### Production Build

```bash
# Frontend
cd frontend
npm run build
# Output in dist/

# Backend - no build needed, run with:
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Environment Variables

Create `.env` file in backend directory:
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/ghostide
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key-here
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Monaco Editor by Microsoft
- FastAPI framework
- Docker for secure execution environments
- The spooky coding community 👻ke8 .                        # Lint code
```

## Docker Commands

```bash
docker-compose up -d             # Start all services
docker-compose down              # Stop all services
docker-compose logs backend      # View backend logs
docker-compose exec backend bash # Access backend container
```