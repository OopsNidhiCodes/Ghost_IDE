#!/usr/bin/env python3
"""
Python code execution script for GhostIDE
Executes user code with security restrictions
"""

import sys
import os
import subprocess
import tempfile
import signal
from pathlib import Path

def execute_code():
    """Execute Python code from stdin"""
    try:
        # Read code from stdin
        code = sys.stdin.read()
        
        # Create temporary file for code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Execute the code with timeout
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd='/tmp'  # Run in safe directory
            )
            
            # Output results
            if result.stdout:
                print(result.stdout, end='')
            if result.stderr:
                print(result.stderr, end='', file=sys.stderr)
            
            sys.exit(result.returncode)
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file)
            
    except subprocess.TimeoutExpired:
        print("Error: Code execution timed out (30 seconds)", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    execute_code()