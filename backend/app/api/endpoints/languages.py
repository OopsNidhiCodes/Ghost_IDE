"""
Language Management API endpoints
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.services.language_manager import language_manager
from app.services.code_execution import code_execution_service

router = APIRouter()


class LanguageInfo(BaseModel):
    """Language information response model"""
    name: str
    extension: str
    monaco_language: str
    icon: str
    color: str
    template: str
    examples: List[Dict[str, str]]


class ValidationRequest(BaseModel):
    """Code validation request model"""
    code: str
    language: str


class ValidationResponse(BaseModel):
    """Code validation response model"""
    is_valid: bool
    issues: List[Dict[str, Any]]


class DetectionRequest(BaseModel):
    """Language detection request model"""
    filename: Optional[str] = None
    content: Optional[str] = None


class DetectionResponse(BaseModel):
    """Language detection response model"""
    detected_language: Optional[str]
    confidence: str  # high, medium, low


@router.get("/languages", response_model=List[str])
async def get_supported_languages():
    """Get list of supported programming languages"""
    return language_manager.get_supported_languages()


@router.get("/languages/{language}", response_model=LanguageInfo)
async def get_language_info(language: str):
    """Get detailed information about a specific language"""
    config = language_manager.get_language_config(language)
    if not config:
        raise HTTPException(status_code=404, detail=f"Language '{language}' not supported")
    
    return LanguageInfo(
        name=config.name,
        extension=config.extension,
        monaco_language=config.monaco_language,
        icon=config.icon,
        color=config.color,
        template=config.template,
        examples=config.examples
    )


@router.get("/languages/{language}/template")
async def get_language_template(language: str):
    """Get template code for a specific language"""
    template = language_manager.get_language_template(language)
    if template is None:
        raise HTTPException(status_code=404, detail=f"Language '{language}' not supported")
    
    return {"template": template}


@router.get("/languages/{language}/examples")
async def get_language_examples(language: str):
    """Get example code snippets for a specific language"""
    examples = language_manager.get_language_examples(language)
    if not language_manager.get_language_config(language):
        raise HTTPException(status_code=404, detail=f"Language '{language}' not supported")
    
    return {"examples": examples}


@router.post("/languages/validate", response_model=ValidationResponse)
async def validate_code(request: ValidationRequest):
    """Validate code against language-specific rules"""
    is_valid, issues = language_manager.validate_code(request.code, request.language)
    
    return ValidationResponse(
        is_valid=is_valid,
        issues=issues
    )


@router.post("/languages/detect", response_model=DetectionResponse)
async def detect_language(request: DetectionRequest):
    """Detect programming language from filename and/or content"""
    if not request.filename and not request.content:
        raise HTTPException(status_code=400, detail="Either filename or content must be provided")
    
    detected = None
    confidence = "low"
    
    # Try filename first
    if request.filename:
        detected = language_manager.detect_language_from_filename(request.filename)
        if detected:
            confidence = "high"
    
    # Try content if filename detection failed or wasn't provided
    if not detected and request.content:
        detected = language_manager.detect_language_from_content(request.content)
        if detected:
            confidence = "medium" if request.filename else "high"
    
    return DetectionResponse(
        detected_language=detected,
        confidence=confidence
    )


@router.post("/languages/detect/file")
async def detect_language_from_file(file: UploadFile = File(...)):
    """Detect programming language from uploaded file"""
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8', errors='ignore')
        
        detected = None
        confidence = "low"
        
        # Try filename first
        if file.filename:
            detected = language_manager.detect_language_from_filename(file.filename)
            if detected:
                confidence = "high"
        
        # Try content if filename detection failed
        if not detected and content_str:
            detected = language_manager.detect_language_from_content(content_str)
            if detected:
                confidence = "medium"
        
        return {
            "detected_language": detected,
            "confidence": confidence,
            "filename": file.filename,
            "content_preview": content_str[:200] + "..." if len(content_str) > 200 else content_str
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File content is not valid text")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")


@router.get("/languages/{language}/config")
async def get_language_config(language: str):
    """Get complete language configuration (for debugging/admin)"""
    config = language_manager.get_language_config(language)
    if not config:
        raise HTTPException(status_code=404, detail=f"Language '{language}' not supported")
    
    return {
        "name": config.name,
        "extension": config.extension,
        "monaco_language": config.monaco_language,
        "icon": config.icon,
        "color": config.color,
        "docker_image": config.docker_image,
        "dockerfile": config.dockerfile,
        "compiler_config": {
            "command": config.compiler_config.command,
            "args": config.compiler_config.args,
            "compile_command": config.compiler_config.compile_command,
            "compile_args": config.compiler_config.compile_args,
            "timeout": config.compiler_config.timeout,
            "memory_limit": config.compiler_config.memory_limit,
            "cpu_quota": config.compiler_config.cpu_quota
        },
        "validation_rules_count": len(config.validation_rules),
        "error_patterns_count": len(config.error_patterns),
        "examples_count": len(config.examples),
        "file_patterns": config.file_patterns,
        "mime_types": config.mime_types
    }