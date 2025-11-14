FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install security updates and basic tools
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 coderunner
USER coderunner

# Set resource limits
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Copy and set permissions for execution script
COPY --chown=coderunner:coderunner execute.py /app/
RUN chmod +x /app/execute.py

# Default command
CMD ["python", "/app/execute.py"]