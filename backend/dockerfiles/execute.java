#!/bin/bash
# Java code execution script for GhostIDE
# Executes user code with security restrictions

set -e

# Read code from stdin
CODE=$(cat)

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Write code to Main.java (Java requires class name to match filename)
echo "$CODE" > Main.java

# Compile the code
if ! javac Main.java 2>&1; then
    echo "Compilation failed" >&2
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Execute with timeout
timeout 30s java Main 2>&1 || {
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo "Error: Code execution timed out (30 seconds)" >&2
        exit 1
    else
        exit $exit_code
    fi
}

# Clean up
rm -rf "$TEMP_DIR"