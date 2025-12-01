FROM node:18-slim

# Set working directory
WORKDIR /app

# Install security updates
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Use existing node user (UID 1000 already exists)
USER node

# Default command (overridden at runtime)
CMD ["node"]