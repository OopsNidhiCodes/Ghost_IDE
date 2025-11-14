# GhostIDE

A spooky online IDE with an AI assistant that provides darkly humorous coding guidance.

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
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   └── services/       # Business logic services
│   ├── tests/              # Backend tests
│   └── requirements.txt    # Python dependencies
└── docker-compose.yml      # Development environment
```

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ghost-ide
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the development environment**
   ```bash
   docker-compose up -d
   ```

4. **Install frontend dependencies (if running locally)**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Install backend dependencies (if running locally)**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

## Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Technology Stack

### Frontend
- React 18 with TypeScript
- Vite for build tooling
- Monaco Editor for code editing
- Socket.io for real-time communication
- Zustand for state management
- Tailwind CSS with custom spooky theme

### Backend
- Python FastAPI
- PostgreSQL with SQLAlchemy
- Redis for caching and Celery broker
- Celery for async task processing
- Docker for code execution isolation
- OpenAI API for Ghost AI assistant

## Development Commands

### Frontend
```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run test         # Run tests
npm run lint         # Run ESLint
```

### Backend
```bash
uvicorn app.main:app --reload    # Start development server
pytest                           # Run tests
black .                          # Format code
flake8 .                        # Lint code
```

## Docker Commands

```bash
docker-compose up -d             # Start all services
docker-compose down              # Stop all services
docker-compose logs backend      # View backend logs
docker-compose exec backend bash # Access backend container
```