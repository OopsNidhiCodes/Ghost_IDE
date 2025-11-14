#!/usr/bin/env python3
"""
Script to build all Docker containers for code execution
"""

import docker
import sys
from pathlib import Path
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_containers():
    """Build all Docker containers for supported languages"""
    
    # Language configurations
    languages = {
        'python': {
            'image': 'ghostide-python',
            'dockerfile': 'python.Dockerfile'
        },
        'javascript': {
            'image': 'ghostide-javascript', 
            'dockerfile': 'javascript.Dockerfile'
        },
        'java': {
            'image': 'ghostide-java',
            'dockerfile': 'java.Dockerfile'
        },
        'cpp': {
            'image': 'ghostide-cpp',
            'dockerfile': 'cpp.Dockerfile'
        }
    }
    
    # Get Docker client
    try:
        client = docker.from_env()
        logger.info("Connected to Docker daemon")
    except Exception as e:
        logger.error(f"Failed to connect to Docker: {e}")
        return False
    
    # Get dockerfiles path
    dockerfiles_path = Path(__file__).parent.parent / "dockerfiles"
    if not dockerfiles_path.exists():
        logger.error(f"Dockerfiles directory not found: {dockerfiles_path}")
        return False
    
    # Build each container
    success_count = 0
    for lang, config in languages.items():
        try:
            logger.info(f"Building {config['image']} for {lang}...")
            
            # Build the image
            image, build_logs = client.images.build(
                path=str(dockerfiles_path),
                dockerfile=config['dockerfile'],
                tag=config['image'],
                rm=True,
                pull=True
            )
            
            # Log build output
            for log in build_logs:
                if 'stream' in log:
                    logger.debug(log['stream'].strip())
            
            logger.info(f"Successfully built {config['image']}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"Failed to build {config['image']}: {e}")
    
    logger.info(f"Built {success_count}/{len(languages)} containers successfully")
    return success_count == len(languages)

def test_containers():
    """Test that all containers can run basic code"""
    
    test_codes = {
        'ghostide-python': 'print("Hello from Python!")',
        'ghostide-javascript': 'console.log("Hello from JavaScript!");',
        'ghostide-java': '''public class Main {
    public static void main(String[] args) {
        System.out.println("Hello from Java!");
    }
}''',
        'ghostide-cpp': '''#include <iostream>
int main() {
    std::cout << "Hello from C++!" << std::endl;
    return 0;
}'''
    }
    
    try:
        client = docker.from_env()
    except Exception as e:
        logger.error(f"Failed to connect to Docker: {e}")
        return False
    
    success_count = 0
    for image, code in test_codes.items():
        try:
            logger.info(f"Testing {image}...")
            
            # Run container with test code
            result = client.containers.run(
                image,
                stdin_open=True,
                stdout=True,
                stderr=True,
                remove=True,
                mem_limit='128m',
                cpu_quota=50000,
                network_disabled=True,
                read_only=True,
                tmpfs={'/tmp': 'rw,noexec,nosuid,size=10m'},
                user='1000:1000',
                input=code.encode('utf-8')
            )
            
            output = result.decode('utf-8', errors='replace')
            if "Hello from" in output:
                logger.info(f"✓ {image} test passed")
                success_count += 1
            else:
                logger.error(f"✗ {image} test failed - unexpected output: {output}")
                
        except Exception as e:
            logger.error(f"✗ {image} test failed: {e}")
    
    logger.info(f"Tested {success_count}/{len(test_codes)} containers successfully")
    return success_count == len(test_codes)

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        success = test_containers()
    else:
        success = build_containers()
        if success:
            logger.info("Running container tests...")
            success = test_containers()
    
    if success:
        logger.info("All operations completed successfully!")
        sys.exit(0)
    else:
        logger.error("Some operations failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()