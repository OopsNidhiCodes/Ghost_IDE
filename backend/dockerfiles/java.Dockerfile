FROM eclipse-temurin:17-jdk-alpine

# Set working directory
WORKDIR /app

# Install security updates (Alpine uses apk)
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# Use existing user or create if needed
RUN id -u 1000 || adduser -D -u 1000 coderunner

# Switch to non-root user
USER 1000

# Default command (overridden at runtime)
CMD ["java"]