FROM node:18-slim

# Set working directory
WORKDIR /app

# Install security updates
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 coderunner
USER coderunner

# Copy and set permissions for execution script
COPY --chown=coderunner:coderunner execute.js /app/
RUN chmod +x /app/execute.js

# Default command
CMD ["node", "/app/execute.js"]