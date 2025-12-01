FROM gcc:13

# Set working directory
WORKDIR /app

# Install security updates
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd -m -u 1000 coderunner
USER coderunner

# Default command (overridden at runtime)
CMD ["g++"]