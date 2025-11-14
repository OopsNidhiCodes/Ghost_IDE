#!/usr/bin/env python3
"""
Integration Test Script for GhostIDE
Tests the complete end-to-end functionality
"""

import asyncio
import json
import time
from typing import Dict, Any

import requests
import websockets
from websockets.exceptions import ConnectionClosed


class GhostIDEIntegrationTest:
    """Integration test for complete GhostIDE workflow"""
    
    def __init__(self, backend_url: str = "http://localhost:8000"):
        self.backend_url = backend_url
        self.api_url = f"{backend_url}/api/v1"
        self.ws_url = backend_url.replace("http", "ws")
        self.session_id = None
        self.file_id = None
        
    def test_api_health(self) -> bool:
        """Test API health check"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def test_session_creation(self) -> bool:
        """Test session creation"""
        try:
            response = requests.post(f"{self.api_url}/sessions", json={
                "current_language": "python",
                "preferences": {"theme": "ghost-dark", "font_size": 14}
            })
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success") and data.get("session"):
                    self.session_id = data["session"]["id"]
                    print(f"✅ Session created: {self.session_id}")
                    return True
                else:
                    print(f"❌ Session creation failed: Invalid response format")
                    return False
            else:
                print(f"❌ Session creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Session creation error: {e}")
            return False
    
    def test_file_operations(self) -> bool:
        """Test file creation and management"""
        if not self.session_id:
            return False
            
        try:
            # Create file
            file_data = {
                "name": "test.py",
                "content": 'print("Hello, Ghost IDE!")\nprint("Integration test successful!")',
                "language": "python"
            }
            
            response = requests.post(
                f"{self.api_url}/sessions/{self.session_id}/files",
                json=file_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.file_id = data.get("id")
                print(f"✅ File created: {self.file_id}")
                return True
            else:
                print(f"❌ File creation failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ File creation error: {e}")
            return False
    
    def test_code_execution(self) -> bool:
        """Test code execution"""
        if not self.session_id:
            return False
            
        try:
            execution_data = {
                "code": 'print("Hello, Ghost IDE!")\nprint("Integration test successful!")',
                "language": "python",
                "session_id": self.session_id
            }
            
            response = requests.post(
                f"{self.api_url}/execution/execute",
                json=execution_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if "Hello, Ghost IDE!" in result.get("stdout", ""):
                    print("✅ Code execution successful")
                    return True
                else:
                    print(f"❌ Unexpected output: {result}")
                    return False
            else:
                print(f"❌ Code execution failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Code execution error: {e}")
            return False
    
    def test_language_switching(self) -> bool:
        """Test language switching"""
        if not self.session_id:
            return False
            
        try:
            # Switch to JavaScript
            response = requests.put(
                f"{self.api_url}/sessions/{self.session_id}",
                json={"current_language": "javascript"}
            )
            
            if response.status_code == 200:
                print("✅ Language switched to JavaScript")
                
                # Test JavaScript execution
                js_code = {
                    "code": 'console.log("Hello from JavaScript!");',
                    "language": "javascript",
                    "session_id": self.session_id
                }
                
                exec_response = requests.post(
                    f"{self.api_url}/execution/execute",
                    json=js_code
                )
                
                if exec_response.status_code == 200:
                    print("✅ JavaScript execution successful")
                    return True
                else:
                    print(f"❌ JavaScript execution failed: {exec_response.status_code}")
                    return False
            else:
                print(f"❌ Language switch failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Language switching error: {e}")
            return False
    
    def test_ghost_ai_chat(self) -> bool:
        """Test Ghost AI chat functionality"""
        if not self.session_id:
            return False
            
        try:
            chat_data = {
                "message": "Hello Ghost! Can you help me with my code?",
                "context": {
                    "current_code": 'console.log("Hello from JavaScript!");',
                    "language": "javascript"
                }
            }
            
            response = requests.post(
                f"{self.api_url}/ghost/chat/{self.session_id}",
                json=chat_data
            )
            
            if response.status_code == 200:
                result = response.json()
                if "message" in result:
                    print("✅ Ghost AI chat successful")
                    return True
                else:
                    print(f"❌ Unexpected AI response: {result}")
                    return False
            else:
                print(f"❌ Ghost AI chat failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Ghost AI chat error: {e}")
            return False
    
    async def test_websocket_connection(self) -> bool:
        """Test WebSocket real-time communication"""
        if not self.session_id:
            return False
            
        try:
            uri = f"{self.ws_url}/ws/{self.session_id}"
            
            async with websockets.connect(uri) as websocket:
                print("✅ WebSocket connected")
                
                # Test code execution via WebSocket
                execution_message = {
                    "type": "execute_code",
                    "data": {
                        "code": 'print("WebSocket test successful!")',
                        "language": "python",
                        "session_id": self.session_id
                    }
                }
                
                await websocket.send(json.dumps(execution_message))
                
                # Wait for responses
                responses = []
                timeout = 10  # 10 seconds timeout
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(response)
                        responses.append(data)
                        
                        if data.get("type") == "execution_complete":
                            break
                            
                    except asyncio.TimeoutError:
                        continue
                    except ConnectionClosed:
                        break
                
                if responses:
                    print("✅ WebSocket communication successful")
                    return True
                else:
                    print("❌ No WebSocket responses received")
                    return False
                    
        except Exception as e:
            print(f"❌ WebSocket test error: {e}")
            return False
    
    def test_session_persistence(self) -> bool:
        """Test session data persistence"""
        if not self.session_id:
            return False
            
        try:
            # Get session data
            response = requests.get(f"{self.api_url}/sessions/{self.session_id}")
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success") and response_data.get("session"):
                    session_data = response_data["session"]
                    if session_data.get("id") == self.session_id:
                        print("✅ Session persistence successful")
                        return True
                    else:
                        print(f"❌ Session ID mismatch: expected {self.session_id}, got {session_data.get('id')}")
                        return False
                else:
                    print(f"❌ Session data format error: {response_data}")
                    return False
            else:
                print(f"❌ Session retrieval failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Session persistence error: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("🚀 Starting GhostIDE Integration Tests\n")
        
        results = {}
        
        # API Tests
        print("📡 Testing API functionality...")
        results["health_check"] = self.test_api_health()
        results["session_creation"] = self.test_session_creation()
        results["file_operations"] = self.test_file_operations()
        results["code_execution"] = self.test_code_execution()
        results["language_switching"] = self.test_language_switching()
        results["ghost_ai_chat"] = self.test_ghost_ai_chat()
        results["session_persistence"] = self.test_session_persistence()
        
        # WebSocket Tests
        print("\n🔌 Testing WebSocket functionality...")
        results["websocket_connection"] = await self.test_websocket_connection()
        
        # Summary
        print("\n📊 Test Results Summary:")
        print("=" * 40)
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{test_name.replace('_', ' ').title()}: {status}")
            if result:
                passed += 1
        
        print("=" * 40)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All integration tests passed!")
        else:
            print("⚠️  Some tests failed. Check the logs above.")
        
        return results


async def main():
    """Main test runner"""
    tester = GhostIDEIntegrationTest()
    results = await tester.run_all_tests()
    
    # Exit with error code if any tests failed
    if not all(results.values()):
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())