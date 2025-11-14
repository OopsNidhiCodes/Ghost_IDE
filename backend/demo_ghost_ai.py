#!/usr/bin/env python3
"""
Demo script to showcase Ghost AI Service functionality
"""

import asyncio
import os
from app.services.ghost_ai import (
    GhostAIService, 
    GhostPersonality, 
    AIContext, 
    CodeGenerationRequest,
    HookEvent,
    HookEventType
)
from app.models.schemas import LanguageType


async def demo_ghost_ai():
    """Demonstrate Ghost AI service functionality"""
    print("🎃 Ghost AI Service Demo 🎃")
    print("=" * 50)
    
    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  OpenAI API key not found in environment variables")
        print("   Set OPENAI_API_KEY to test with real AI responses")
        print("   Continuing with mock demonstration...\n")
        api_key = "demo-key"
    
    # Initialize Ghost AI service
    ghost_service = GhostAIService(api_key=api_key)
    
    # Demo 1: Show personality configuration
    print("👻 Ghost Personality Configuration:")
    personality_info = ghost_service.get_personality_info()
    print(f"   Name: {personality_info['name']}")
    print(f"   Traits: {', '.join(personality_info['traits'])}")
    print(f"   Style: {personality_info['vocabulary_style']}")
    print()
    
    # Demo 2: Show spooky variable generation
    print("🕸️  Spooky Variable Names by Level:")
    for level in range(1, 6):
        vars_list = ghost_service._get_spooky_variables(level)
        spooky_vars = [v for v in vars_list if "spectral" in v or "phantom" in v or "cursed" in v or "ethereal" in v][:3]
        print(f"   Level {level}: {', '.join(spooky_vars)}")
    print()
    
    # Demo 3: Show hook event prompts
    print("⚰️  Hook Event Demonstrations:")
    
    # Create sample context
    context = AIContext(
        current_code="print('Hello, Ghost World!')",
        language=LanguageType.PYTHON,
        session_id="demo-session"
    )
    
    # Demo on_run event
    run_event = HookEvent(
        event_type=HookEventType.ON_RUN,
        session_id="demo-session",
        data={"code": "print('Hello, Ghost!')", "language": "python"}
    )
    run_prompt = ghost_service._build_on_run_prompt(run_event, context)
    print(f"   ON_RUN prompt: {run_prompt[:100]}...")
    
    # Demo on_error event
    error_event = HookEvent(
        event_type=HookEventType.ON_ERROR,
        session_id="demo-session",
        data={"error": "SyntaxError: invalid syntax", "code": "print('hello'"}
    )
    error_prompt = ghost_service._build_on_error_prompt(error_event, context)
    print(f"   ON_ERROR prompt: {error_prompt[:100]}...")
    
    # Demo on_save event
    save_event = HookEvent(
        event_type=HookEventType.ON_SAVE,
        session_id="demo-session",
        data={"code": "def hello():\n    return 'world'"}
    )
    save_prompt = ghost_service._build_on_save_prompt(save_event, context)
    print(f"   ON_SAVE prompt: {save_prompt[:100]}...")
    print()
    
    # Demo 4: Show fallback responses
    print("💀 Fallback Responses (when AI is unavailable):")
    fallback_types = ["error", "on_run", "on_error", "on_save", "default"]
    for fb_type in fallback_types:
        response = ghost_service._get_fallback_response(fb_type)
        print(f"   {fb_type}: {response}")
    print()
    
    # Demo 5: Show code generation request structure
    print("🧙‍♂️ Code Generation Request Example:")
    code_request = CodeGenerationRequest(
        description="Create a function to calculate factorial",
        language=LanguageType.PYTHON,
        context="This is for a math tutorial",
        spooky_level=3
    )
    print(f"   Description: {code_request.description}")
    print(f"   Language: {code_request.language}")
    print(f"   Spooky Level: {code_request.spooky_level}")
    print()
    
    # Demo 6: Test with real API if available
    if api_key != "demo-key":
        print("🌟 Testing with Real OpenAI API:")
        try:
            response = await ghost_service.generate_response(
                "Say hello in a spooky way", 
                context
            )
            print(f"   AI Response: {response}")
        except Exception as e:
            print(f"   Error: {e}")
        print()
    
    print("✨ Ghost AI Service Demo Complete! ✨")
    print("The service is ready to haunt your IDE with helpful assistance! 👻")


if __name__ == "__main__":
    asyncio.run(demo_ghost_ai())