FROM openjdk:17-slim

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
COPY --chown=coderunner:coderunner execute.java /app/
RUN chmod +x /app/execute.java

# Default command
CMD ["java", "/app/execute.java"]