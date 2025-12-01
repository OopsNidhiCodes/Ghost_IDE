# Docker Setup for GhostIDE

GhostIDE uses Docker containers to execute code safely and securely across multiple programming languages.

## Why Docker?

- **Security**: Code runs in isolated containers with limited resources
- **Multi-language support**: Python, JavaScript, Java, C++, and more
- **Resource limits**: CPU, memory, and execution time constraints
- **No system pollution**: Code execution doesn't affect your host machine

## Quick Setup

### 1. Install Docker Desktop

Download and install Docker Desktop for your platform:
- **Windows**: https://www.docker.com/products/docker-desktop
- **macOS**: https://www.docker.com/products/docker-desktop
- **Linux**: https://docs.docker.com/engine/install/

### 2. Start Docker Desktop

- Open Docker Desktop application
- Wait for it to fully start (the whale icon will be steady)
- You can verify Docker is running by opening a terminal and typing: `docker version`

### 3. Build Language Containers

From the GhostIDE backend directory, run:

```bash
cd backend
python scripts/build_containers.py
```

This will build Docker images for all supported languages:
- `ghostide-python` - Python 3.12
- `ghostide-javascript` - Node.js
- `ghostide-java` - OpenJDK
- `ghostide-cpp` - GCC/G++

### 4. Restart Backend

If the backend is already running, restart it to detect Docker:

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1  # Windows
source venv/bin/activate      # Linux/macOS

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Development Mode (Python Only)

If you don't want to install Docker for quick testing, GhostIDE supports a **fallback Python execution mode**:

- Python code will run directly on your system (less secure)
- Other languages will show a helpful error message
- **Not recommended for production**

## Troubleshooting

### Docker not detected
- Ensure Docker Desktop is running
- Check that `docker version` works in your terminal
- Try restarting Docker Desktop

### Container build failures
- Make sure you have internet connection
- Check Docker Desktop has enough disk space
- Try pulling base images manually:
  ```bash
  docker pull python:3.12-slim
  docker pull node:20-slim
  docker pull openjdk:17-slim
  ```

### Permission errors (Linux)
- Add your user to the docker group:
  ```bash
  sudo usermod -aG docker $USER
  newgrp docker
  ```

## Container Security

Each container runs with:
- Non-root user (UID 1000)
- Network disabled
- Read-only filesystem
- Memory limit: 256MB
- CPU quota: Limited
- Process limit: 50
- Execution timeout: 30 seconds

## Manual Container Build

If the build script doesn't work, you can build containers manually:

```bash
cd backend/dockerfiles

# Python
docker build -f python.Dockerfile -t ghostide-python .

# JavaScript
docker build -f javascript.Dockerfile -t ghostide-javascript .

# Java
docker build -f java.Dockerfile -t ghostide-java .

# C++
docker build -f cpp.Dockerfile -t ghostide-cpp .
```

## Verifying Installation

Test each language container:

```bash
# Python
docker run --rm ghostide-python python --version

# JavaScript
docker run --rm ghostide-javascript node --version

# Java
docker run --rm ghostide-java java --version

# C++
docker run --rm ghostide-cpp g++ --version
```

All commands should return version information without errors.
