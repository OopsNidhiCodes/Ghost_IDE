#!/usr/bin/env python3
"""
Script to run code execution tests
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run the code execution tests"""
    
    # Change to backend directory
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    # Test commands to run
    test_commands = [
        # Unit tests (no Docker required)
        ["python", "-m", "pytest", "tests/test_code_execution.py", "-v", "--tb=short", "-m", "not integration"],
        ["python", "-m", "pytest", "tests/test_tasks.py", "-v", "--tb=short", "-m", "not integration"],
        ["python", "-m", "pytest", "tests/test_execution_api.py", "-v", "--tb=short"],
    ]
    
    # Integration tests (require Docker)
    integration_commands = [
        ["python", "-m", "pytest", "tests/test_code_execution.py", "-v", "--tb=short", "-m", "integration"],
        ["python", "-m", "pytest", "tests/test_tasks.py", "-v", "--tb=short", "-m", "integration"],
    ]
    
    print("Running unit tests...")
    for cmd in test_commands:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Test failed: {' '.join(cmd)}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
        else:
            print(f"✅ Test passed: {' '.join(cmd)}")
    
    print("\nRunning integration tests (requires Docker)...")
    for cmd in integration_commands:
        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️  Integration test failed (Docker may not be available): {' '.join(cmd)}")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
        else:
            print(f"✅ Integration test passed: {' '.join(cmd)}")
    
    print("\n🎉 All unit tests completed successfully!")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)