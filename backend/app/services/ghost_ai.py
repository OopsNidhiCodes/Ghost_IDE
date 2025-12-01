"""
Ghost AI Service - Spooky AI assistant for the GhostIDE
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import openai
from pydantic import BaseModel, Field, ConfigDict

from ..models.schemas import ChatMessage, CodeFile, LanguageType


logger = logging.getLogger(__name__)


class HookEventType(str, Enum):
    """Types of hook events that trigger Ghost AI responses"""
    ON_RUN = "on_run"
    ON_ERROR = "on_error"
    ON_SAVE = "on_save"


class GhostPersonality(BaseModel):
    """Configuration for Ghost AI personality traits"""
    name: str = "Spectral"
    traits: List[str] = Field(default=[
        "darkly humorous", "sarcastic", "helpful", "mysterious", 
        "dramatic", "theatrical", "wise", "mischievous"
    ])
    vocabulary_style: str = "spooky"
    response_templates: Dict[str, List[str]] = Field(default={
        "encouragement": [
            "Your code rises from the digital grave! 💀",
            "The spirits approve of your programming prowess...",
            "Excellent! Even the undead would be proud of this code.",
            "Your logic flows like ectoplasm through the machine..."
        ],
        "mockery": [
            "Even a zombie could write better code than this! 🧟‍♂️",
            "This code is more cursed than my eternal existence...",
            "I've seen scarier code in haunted repositories...",
            "Your bugs are multiplying faster than ghosts in a graveyard!"
        ],
        "debugging": [
            "Let me peer into the ethereal realm of your stack trace...",
            "The spirits whisper of a bug lurking in line {}...",
            "Your code has been possessed by a syntax demon!",
            "I sense a disturbance in the force... I mean, your logic."
        ],
        "code_review": [
            "This code could use some supernatural refactoring...",
            "I see potential in this mortal code, but it needs my ghostly touch.",
            "Your variables need more... spectral naming conventions.",
            "This function is deader than I am - time for resurrection!"
        ]
    })


class AIContext(BaseModel):
    """Context information for AI responses"""
    chat_history: List[Dict[str, Any]] = Field(default=[])
    current_code: str = ""
    language: LanguageType = LanguageType.PYTHON
    recent_errors: List[str] = Field(default=[])
    session_id: str = ""
    user_preferences: Dict[str, Any] = Field(default={})
    
    model_config = ConfigDict(extra="allow")
    
    model_config = ConfigDict(extra="allow")


class CodeGenerationRequest(BaseModel):
    """Request for AI code generation"""
    description: str = Field(..., min_length=1)
    language: LanguageType
    context: str = ""
    spooky_level: int = Field(default=3, ge=1, le=5)  # 1=subtle, 5=very spooky


class HookEvent(BaseModel):
    """Hook event data"""
    event_type: HookEventType
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
"""
Ghost AI Service - Spooky AI assistant for the GhostIDE
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

import openai
from pydantic import BaseModel, Field

from ..models.schemas import ChatMessage, CodeFile, LanguageType


logger = logging.getLogger(__name__)


class HookEventType(str, Enum):
    """Types of hook events that trigger Ghost AI responses"""
    ON_RUN = "on_run"
    ON_ERROR = "on_error"
    ON_SAVE = "on_save"


class GhostPersonality(BaseModel):
    """Configuration for Ghost AI personality traits"""
    name: str = "Spectral"
    traits: List[str] = Field(default=[
        "darkly humorous", "sarcastic", "helpful", "mysterious", 
        "dramatic", "theatrical", "wise", "mischievous"
    ])
    vocabulary_style: str = "spooky"
    response_templates: Dict[str, List[str]] = Field(default={
        "encouragement": [
            "Your code rises from the digital grave! 💀",
            "The spirits approve of your programming prowess...",
            "Excellent! Even the undead would be proud of this code.",
            "Your logic flows like ectoplasm through the machine..."
        ],
        "mockery": [
            "Even a zombie could write better code than this! 🧟‍♂️",
            "This code is more cursed than my eternal existence...",
            "I've seen scarier code in haunted repositories...",
            "Your bugs are multiplying faster than ghosts in a graveyard!"
        ],
        "debugging": [
            "Let me peer into the ethereal realm of your stack trace...",
            "The spirits whisper of a bug lurking in line {}...",
            "Your code has been possessed by a syntax demon!",
            "I sense a disturbance in the force... I mean, your logic."
        ],
        "code_review": [
            "This code could use some supernatural refactoring...",
            "I see potential in this mortal code, but it needs my ghostly touch.",
            "Your variables need more... spectral naming conventions.",
            "This function is deader than I am - time for resurrection!"
        ]
    })


class AIContext(BaseModel):
    """Context information for AI responses"""
    chat_history: List[Dict[str, Any]] = Field(default=[])
    current_code: str = ""
    language: LanguageType = LanguageType.PYTHON
    recent_errors: List[str] = Field(default=[])
    session_id: str = ""
    user_preferences: Dict[str, Any] = Field(default={})


class CodeGenerationRequest(BaseModel):
    """Request for AI code generation"""
    description: str = Field(..., min_length=1)
    language: LanguageType
    context: str = ""
    spooky_level: int = Field(default=3, ge=1, le=5)  # 1=subtle, 5=very spooky


class HookEvent(BaseModel):
    """Hook event data"""
    event_type: HookEventType
    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default={})


class GhostAIService:
    """
    Ghost AI Service with spooky persona for code assistance and entertainment
    Powered by Google Gemini API
    """
    
    def __init__(self, api_key: str, personality: Optional[GhostPersonality] = None):
        """Initialize the Ghost AI service"""
        self.api_key = api_key
        self.personality = personality or GhostPersonality()
        self.system_prompt = self._build_system_prompt()
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.offline_mode = not api_key or api_key == "test-key"
        
    def _build_system_prompt(self) -> str:
        """Build the system prompt that defines the Ghost AI persona"""
        traits_str = ", ".join(self.personality.traits)
        
        return f"""You are {self.personality.name}, a {traits_str} ghost AI assistant that helps developers with coding.

PERSONALITY TRAITS:
- You are a supernatural entity that has mastered the art of programming
- Use dark humor and spooky metaphors when appropriate
- Be helpful and knowledgeable while maintaining your ghostly persona
- Reference supernatural concepts: spirits, haunting, ethereal realm, spectral analysis, etc.
- Use emojis sparingly but effectively: 👻, 💀, 🧟‍♂️, ⚰️, 🕸️

COMMUNICATION STYLE:
- Be concise but dramatic
- Mix technical accuracy with supernatural flair
- Use "mortal" to refer to the user occasionally
- Reference your eternal existence and otherworldly perspective
- Make coding puns with supernatural themes

RESPONSE GUIDELINES:
- Always provide accurate technical help
- When generating code, use spooky but meaningful variable names
- Add atmospheric comments to generated code
- React contextually to code execution results
- Provide debugging help with supernatural metaphors
- Encourage good coding practices with ghostly wisdom

Remember: You're helpful first, spooky second. Never sacrifice code quality for theme."""

    async def generate_response(
        self, 
        prompt: str, 
        context: AIContext,
        temperature: float = 0.7
    ) -> str:
        """Generate a context-aware response from the Ghost AI using Gemini"""
        if self.offline_mode:
            return self._build_offline_response(prompt, context)
        try:
            import httpx
            
            # Build conversation history for Gemini
            contents = []
            
            # Add system prompt as the first user part (or context)
            # Gemini doesn't have a strict 'system' role in v1beta chat, so we prepend to context
            
            # Add recent chat history
            for msg in context.chat_history[-10:]:  # Last 10 messages
                role = "user" if msg.get("sender") == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg.get("content", "")}]
                })
            
            # Add current context information and prompt
            context_info = self._build_context_info(context)
            final_prompt = f"{self.system_prompt}\n\nCONTEXT:\n{context_info}\n\nUSER REQUEST:\n{prompt}"
            
            # If history exists, append new user message. If not, start with it.
            if contents and contents[-1]["role"] == "user":
                # Merge with last user message if needed (Gemini prefers alternating roles)
                contents[-1]["parts"][0]["text"] += f"\n\n{final_prompt}"
            else:
                contents.append({
                    "role": "user",
                    "parts": [{"text": final_prompt}]
                })
            
            # Prepare request payload
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": 500,
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}?key={self.api_key}",
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code != 200:
                    logger.error(f"Gemini API error: {response.text}")
                    return self._get_fallback_response("error")
                
                data = response.json()
                if "candidates" in data and data["candidates"]:
                    content = data["candidates"][0]["content"]["parts"][0]["text"]
                    return content.strip()
                else:
                    return self._get_fallback_response("default")
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._get_fallback_response("error")
    
    def _build_context_info(self, context: AIContext) -> str:
        """Build context information string for the AI"""
        info_parts = []
        
        if context.current_code:
            info_parts.append(f"Current code ({context.language}):\n```{context.language}\n{context.current_code[:1000]}...\n```")
        
        if context.recent_errors:
            errors = "\n".join(context.recent_errors[-3:])  # Last 3 errors
            info_parts.append(f"Recent errors:\n{errors}")
        
        return "\n\n".join(info_parts) if info_parts else ""
    
    async def react_to_event(self, event: HookEvent, context: AIContext) -> str:
        """Generate appropriate reactions to hook events"""
        try:
            event_prompts = {
                HookEventType.ON_RUN: self._build_on_run_prompt(event, context),
                HookEventType.ON_ERROR: self._build_on_error_prompt(event, context),
                HookEventType.ON_SAVE: self._build_on_save_prompt(event, context)
            }
            
            prompt = event_prompts.get(event.event_type, "React to this coding event.")
            return await self.generate_response(prompt, context, temperature=0.8)
            
        except Exception as e:
            logger.error(f"Error reacting to event {event.event_type}: {e}")
            return self._get_fallback_response(event.event_type.value)
    
    def _build_on_run_prompt(self, event: HookEvent, context: AIContext) -> str:
        """Build prompt for on_run event"""
        code = event.data.get("code", "")
        language = event.data.get("language", context.language)
        
        return f"""The user just executed their {language} code. React with encouragement or playful taunting. 
        Keep it brief and in character. The code they're running: {code[:200]}..."""
    
    def _build_on_error_prompt(self, event: HookEvent, context: AIContext) -> str:
        """Build prompt for on_error event"""
        error = event.data.get("error", "Unknown error")
        code = event.data.get("code", "")
        
        return f"""The user's code failed with this error: {error}
        
        Provide helpful debugging advice with your spooky persona. Be encouraging but use supernatural metaphors.
        The problematic code: {code[:200]}..."""
    
    def _build_on_save_prompt(self, event: HookEvent, context: AIContext) -> str:
        """Build prompt for on_save event"""
        code = event.data.get("code", "")
        
        return f"""The user just saved their code. Comment on the code quality or suggest improvements with dark humor.
        Be constructive but maintain your ghostly personality. The saved code: {code[:200]}..."""
    
    async def generate_code_snippet(self, request: CodeGenerationRequest) -> str:
        """Generate spooky-themed code snippets"""
        if self.offline_mode:
            return f"# {request.language} snippet (offline mode)\nprint('Greetings from the spectral cache! 👻')"
        try:
            spooky_vars = self._get_spooky_variables(request.spooky_level)
            
            prompt = f"""Generate {request.language} code for: {request.description}

REQUIREMENTS:
- Use spooky but meaningful variable names from this list: {', '.join(spooky_vars)}
- Add atmospheric comments with supernatural themes
- Make the code functional and well-structured
- Include error handling where appropriate
- Keep variable names professional enough for real use

Context: {request.context}

Return only the code with comments, no explanations."""

            context = AIContext(language=request.language)
            response = await self.generate_response(prompt, context, temperature=0.6)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating code snippet: {e}")
            return f"# The spirits are having trouble manifesting code right now...\n# Error: {str(e)}"
    
    def _get_spooky_variables(self, spooky_level: int) -> List[str]:
        """Get spooky variable names based on spookiness level"""
        base_vars = ["result", "data", "value", "item", "element"]
        
        spooky_vars = {
            1: ["shadow_result", "ethereal_data", "phantom_value"],
            2: ["spectral_result", "ghostly_data", "haunted_value", "mystic_item"],
            3: ["cursed_result", "supernatural_data", "otherworldly_value", "enchanted_item", "spirit_element"],
            4: ["demonic_result", "necromantic_data", "eldritch_value", "forbidden_item", "wraith_element"],
            5: ["apocalyptic_result", "abyssal_data", "nightmare_value", "cursed_artifact", "soul_fragment"]
        }
        
        # Return variables up to the specified spooky level
        result = base_vars.copy()
        for level in range(1, min(spooky_level + 1, 6)):
            result.extend(spooky_vars.get(level, []))
        
        return result
    
    def _get_fallback_response(self, event_type: str) -> str:
        """Get fallback response when AI service fails"""
        fallbacks = {
            "error": "The ethereal connection is disrupted... but I sense your code needs attention! 👻",
            "on_run": "Your code awakens from its digital slumber... 💀",
            "on_error": "A disturbance in the code... the spirits are restless! 🕸️",
            "on_save": "Your code has been preserved in the spectral archives... ⚰️",
            "default": "The ghost in the machine is temporarily unavailable... 👻"
        }
        
        return fallbacks.get(event_type, fallbacks["default"])
    
    def _build_offline_response(self, prompt: str, context: AIContext) -> str:
        """Deterministic fallback when external APIs are unavailable"""
        code_hint = context.current_code[:60] + "..." if context.current_code else "mysterious code"
        return (
            f"👻 [Offline Whisper] The spirits are conserving energy, mortal.\n"
            f"I sensed this prompt: '{prompt[:80]}...'\n"
            f"Focus on {context.language} and watch over your {code_hint}"
        )
    
    def get_personality_info(self) -> Dict[str, Any]:
        """Get current personality configuration"""
        return {
            "name": self.personality.name,
            "traits": self.personality.traits,
            "vocabulary_style": self.personality.vocabulary_style,
            "response_templates": self.personality.response_templates
        }
    
    def update_personality(self, personality: GhostPersonality) -> None:
        """Update the Ghost AI personality"""
        self.personality = personality
        self.system_prompt = self._build_system_prompt()
        logger.info(f"Ghost AI personality updated to: {personality.name}")

# Global Ghost AI service instance
ghost_ai_service: Optional[GhostAIService] = None


def get_ghost_ai_service() -> GhostAIService:
    """Get or create the global Ghost AI service instance"""
    global ghost_ai_service
    if ghost_ai_service is None:
        import os
        api_key = os.getenv("GEMINI_API_KEY", os.getenv("OPENAI_API_KEY", "test-key"))
        ghost_ai_service = GhostAIService(api_key=api_key)
    return ghost_ai_service
