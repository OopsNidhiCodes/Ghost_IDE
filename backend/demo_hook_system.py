#!/usr/bin/env python3
"""
Demo script for the GhostIDE Hook System
Shows how the hook system integrates with code execution and AI responses
"""

import asyncio
import os
from datetime import datetime

# Set up environment
os.environ["OPENAI_API_KEY"] = "test-key-for-demo"

from app.services.ghost_ai import GhostAIService
from app.services.hook_manager import HookManagerService, HookEventType
from app.models.schemas import ExecutionRequest, LanguageType


async def demo_hook_system():
    """Demonstrate the hook system functionality"""
    print("🎭 GhostIDE Hook System Demo 👻")
    print("=" * 50)
    
    # Initialize Ghost AI service
    print("\n1. Initializing Ghost AI Service...")
    ghost_ai = GhostAIService(api_key="test-key")
    print("   ✅ Ghost AI Service initialized")
    
    # Initialize Hook Manager
    print("\n2. Initializing Hook Manager...")
    hook_manager = HookManagerService(ghost_ai)
    print("   ✅ Hook Manager initialized")
    print(f"   📊 Enabled hooks: {list(hook_manager.enabled_hooks.keys())}")
    
    # Demo session data
    session_id = "demo-session-123"
    test_code = """
def greet_ghost():
    print("Hello from the spectral realm! 👻")
    return "Boo!"

greet_ghost()
"""
    
    # Demo 1: on_run hook
    print("\n3. Demonstrating on_run hook...")
    print(f"   🏃 Triggering on_run hook for session: {session_id}")
    
    try:
        response = await hook_manager.on_run_hook(
            session_id=session_id,
            code=test_code,
            language="python"
        )
        print(f"   🤖 AI Response: {response}")
    except Exception as e:
        print(f"   ❌ Error (expected with test key): {e}")
    
    # Demo 2: on_error hook
    print("\n4. Demonstrating on_error hook...")
    error_code = "print(undefined_variable)"
    error_message = "NameError: name 'undefined_variable' is not defined"
    
    print(f"   💥 Triggering on_error hook with error: {error_message}")
    
    try:
        response = await hook_manager.on_error_hook(
            session_id=session_id,
            code=error_code,
            language="python",
            error=error_message
        )
        print(f"   🤖 AI Response: {response}")
    except Exception as e:
        print(f"   ❌ Error (expected with test key): {e}")
    
    # Demo 3: on_save hook
    print("\n5. Demonstrating on_save hook...")
    save_code = """
class GhostClass:
    def __init__(self):
        self.spookiness = 100
    
    def haunt(self):
        return f"Haunting with {self.spookiness}% spookiness! 👻"
"""
    
    print(f"   💾 Triggering on_save hook for file: ghost_class.py")
    
    try:
        response = await hook_manager.on_save_hook(
            session_id=session_id,
            code=save_code,
            language="python",
            filename="ghost_class.py"
        )
        print(f"   🤖 AI Response: {response}")
    except Exception as e:
        print(f"   ❌ Error (expected with test key): {e}")
    
    # Demo 4: Hook statistics
    print("\n6. Hook Statistics...")
    stats = hook_manager.get_hook_statistics()
    print(f"   📈 Total events: {stats['total_events']}")
    print(f"   ✅ Successful responses: {stats['successful_responses']}")
    print(f"   ❌ Failed responses: {stats['failed_responses']}")
    print(f"   📊 Success rate: {stats['success_rate']:.1f}%")
    
    # Demo 5: Hook execution history
    print("\n7. Hook Execution History...")
    executions = hook_manager.get_hook_executions(limit=5)
    print(f"   📋 Recent executions: {len(executions)}")
    
    for i, execution in enumerate(executions, 1):
        print(f"   {i}. {execution.event.event_type.value} - {execution.status.value}")
        if execution.error:
            print(f"      Error: {execution.error}")
        if execution.execution_time:
            print(f"      Duration: {execution.execution_time:.3f}s")
    
    # Demo 6: Enable/Disable hooks
    print("\n8. Hook Management...")
    print(f"   🔧 Disabling on_run hook...")
    hook_manager.disable_hook(HookEventType.ON_RUN)
    print(f"   ✅ on_run hook disabled: {not hook_manager.is_hook_enabled(HookEventType.ON_RUN)}")
    
    print(f"   🔧 Re-enabling on_run hook...")
    hook_manager.enable_hook(HookEventType.ON_RUN)
    print(f"   ✅ on_run hook enabled: {hook_manager.is_hook_enabled(HookEventType.ON_RUN)}")
    
    # Demo 7: Custom event listener
    print("\n9. Custom Event Listener...")
    
    listener_events = []
    
    async def custom_listener(event, response):
        listener_events.append({
            "type": event.event_type.value,
            "session": event.session_id,
            "timestamp": datetime.now().isoformat()
        })
        print(f"   🎧 Custom listener received: {event.event_type.value}")
    
    hook_manager.register_event_listener(HookEventType.ON_SAVE, custom_listener)
    
    try:
        await hook_manager.on_save_hook(
            session_id=session_id,
            code="# Test listener",
            language="python",
            filename="test_listener.py"
        )
    except Exception as e:
        print(f"   ❌ Error (expected): {e}")
    
    print(f"   📝 Listener captured {len(listener_events)} events")
    
    print("\n🎉 Hook System Demo Complete! 👻")
    print("=" * 50)


def demo_hook_integration():
    """Show how hooks integrate with the broader system"""
    print("\n🔗 Hook Integration Overview")
    print("-" * 30)
    
    print("The hook system integrates with:")
    print("  • Code Execution Service - triggers on_run and on_error hooks")
    print("  • Session Management - triggers on_save hooks when files are saved")
    print("  • WebSocket Manager - sends AI responses to connected clients")
    print("  • Ghost AI Service - generates contextual responses")
    
    print("\nHook Flow:")
    print("  1. User action occurs (run code, save file, encounter error)")
    print("  2. Relevant service triggers appropriate hook")
    print("  3. Hook Manager calls Ghost AI Service")
    print("  4. AI generates spooky, contextual response")
    print("  5. Response sent to user via WebSocket")
    print("  6. Hook execution logged for debugging/analytics")
    
    print("\nAPI Endpoints:")
    print("  • GET /api/v1/hooks/status - Hook system status")
    print("  • GET /api/v1/hooks/executions - Hook execution history")
    print("  • POST /api/v1/hooks/enable/{type} - Enable specific hook")
    print("  • POST /api/v1/hooks/disable/{type} - Disable specific hook")
    print("  • POST /api/v1/hooks/test/{type} - Test hook manually")


if __name__ == "__main__":
    print("Starting GhostIDE Hook System Demo...")
    
    # Run the async demo
    asyncio.run(demo_hook_system())
    
    # Show integration info
    demo_hook_integration()
    
    print("\n👻 Demo complete! The spirits are pleased with the hook system! 👻")