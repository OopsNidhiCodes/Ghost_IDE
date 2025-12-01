"""
Security middleware for GhostIDE
Implements comprehensive security measures including rate limiting, input validation, and security logging
"""

import re
import time
import logging
import hashlib
from typing import Dict, List, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import asyncio

logger = logging.getLogger(__name__)

# Security patterns for code validation
# Since code runs in isolated Docker containers with resource limits,
# we only block the most dangerous operations (code injection attacks)
DANGEROUS_PATTERNS = [
    # Code injection - these can bypass Docker isolation
    r'import\s+ctypes',
    r'from\s+ctypes\s+import',
]

# Compile patterns for better performance
COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in DANGEROUS_PATTERNS]


class RateLimiter:
    """Rate limiter with sliding window algorithm"""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        
        # Rate limits (requests per minute)
        self.limits = {
            'code_execution': 10,  # 10 code executions per minute
            'ai_requests': 20,     # 20 AI requests per minute
            'api_requests': 100,   # 100 general API requests per minute
        }
        
        # Block duration for rate limit violations (minutes)
        self.block_duration = 15
    
    def is_allowed(self, client_ip: str, endpoint_type: str = 'api_requests') -> bool:
        """Check if request is allowed based on rate limits"""
        now = datetime.now()
        
        # Check if IP is currently blocked
        if client_ip in self.blocked_ips:
            if now < self.blocked_ips[client_ip]:
                return False
            else:
                # Unblock IP
                del self.blocked_ips[client_ip]
        
        # Get rate limit for endpoint type
        limit = self.limits.get(endpoint_type, self.limits['api_requests'])
        
        # Clean old requests (older than 1 minute)
        key = f"{client_ip}:{endpoint_type}"
        cutoff = now - timedelta(minutes=1)
        
        while self.requests[key] and self.requests[key][0] < cutoff:
            self.requests[key].popleft()
        
        # Check if limit exceeded
        if len(self.requests[key]) >= limit:
            # Block IP
            self.blocked_ips[client_ip] = now + timedelta(minutes=self.block_duration)
            logger.warning(f"Rate limit exceeded for IP {client_ip} on {endpoint_type}. Blocked for {self.block_duration} minutes.")
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining_requests(self, client_ip: str, endpoint_type: str = 'api_requests') -> int:
        """Get remaining requests for client"""
        limit = self.limits.get(endpoint_type, self.limits['api_requests'])
        key = f"{client_ip}:{endpoint_type}"
        
        # Clean old requests
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        while self.requests[key] and self.requests[key][0] < cutoff:
            self.requests[key].popleft()
        
        return max(0, limit - len(self.requests[key]))


class InputValidator:
    """Input validation and sanitization"""
    
    @staticmethod
    def validate_code(code: str, language: str) -> tuple[bool, Optional[str]]:
        """Validate user code for security issues"""
        if not code or not isinstance(code, str):
            return False, "Code cannot be empty"
        
        # Check code length
        if len(code) > 50000:  # 50KB limit
            return False, "Code exceeds maximum length of 50,000 characters"
        
        # Check for dangerous patterns
        for pattern in COMPILED_PATTERNS:
            if pattern.search(code):
                return False, f"Code contains potentially dangerous operations: {pattern.pattern}"
        
        # Language-specific validation
        if language.lower() == 'python':
            return InputValidator._validate_python_code(code)
        elif language.lower() == 'javascript':
            return InputValidator._validate_javascript_code(code)
        elif language.lower() in ['java', 'cpp', 'c']:
            return InputValidator._validate_compiled_code(code, language)
        
        return True, None
    
    @staticmethod
    def _validate_python_code(code: str) -> tuple[bool, Optional[str]]:
        """Python-specific validation"""
        # Only block truly dangerous imports (code runs in isolated Docker container)
        dangerous_imports = [
            'ctypes', 'imp', 'importlib.__import__'
        ]
        
        for imp in dangerous_imports:
            if re.search(rf'\bimport\s+{imp}\b|\bfrom\s+{imp}\s+import\b', code, re.IGNORECASE):
                return False, f"Import of '{imp}' module is not allowed"
        
        # Check for dangerous functions
        dangerous_funcs = ['exec', 'eval', 'compile', '__import__']
        for func in dangerous_funcs:
            if re.search(rf'\b{func}\s*\(', code, re.IGNORECASE):
                return False, f"Use of '{func}' function is not allowed"
        
        return True, None
    
    @staticmethod
    def _validate_javascript_code(code: str) -> tuple[bool, Optional[str]]:
        """JavaScript-specific validation"""
        # Allow basic operations - Docker container provides isolation
        return True, None
    
    @staticmethod
    def _validate_compiled_code(code: str, language: str) -> tuple[bool, Optional[str]]:
        """Validation for compiled languages (Java, C, C++)"""
        # Docker containers provide isolation, so allow standard libraries
        # Only block truly dangerous system-level operations
        dangerous_patterns = [
            r'\bsystem\s*\(',  # system() calls
            r'\bexec[vl][pe]*\s*\(',  # exec family
            r'\bfork\s*\(',  # process forking
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Use of dangerous system call is not allowed"
        
        return True, None
    
    @staticmethod
    def sanitize_input(text: str, max_length: int = 1000) -> str:
        """Sanitize general text input"""
        if not text:
            return ""
        
        # Truncate if too long
        text = text[:max_length]
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\']', '', text)
        
        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        return text.strip()


class SecurityLogger:
    """Security event logging"""
    
    def __init__(self):
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.INFO)
        
        # Create file handler for security logs
        handler = logging.FileHandler('security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.security_logger.addHandler(handler)
    
    def log_security_event(self, event_type: str, client_ip: str, details: Dict):
        """Log security events"""
        log_entry = {
            'event_type': event_type,
            'client_ip': client_ip,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        self.security_logger.warning(f"SECURITY_EVENT: {log_entry}")
    
    def log_rate_limit_violation(self, client_ip: str, endpoint: str, limit: int):
        """Log rate limit violations"""
        self.log_security_event(
            'RATE_LIMIT_VIOLATION',
            client_ip,
            {'endpoint': endpoint, 'limit': limit}
        )
    
    def log_input_validation_failure(self, client_ip: str, validation_type: str, reason: str):
        """Log input validation failures"""
        self.log_security_event(
            'INPUT_VALIDATION_FAILURE',
            client_ip,
            {'validation_type': validation_type, 'reason': reason}
        )
    
    def log_suspicious_activity(self, client_ip: str, activity: str, details: Dict):
        """Log suspicious activities"""
        self.log_security_event(
            'SUSPICIOUS_ACTIVITY',
            client_ip,
            {'activity': activity, **details}
        )


class SecurityMiddleware(BaseHTTPMiddleware):
    """Main security middleware"""
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        self.security_logger = SecurityLogger()
        self.validator = InputValidator()
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security checks"""
        client_ip = self._get_client_ip(request)
        
        # Determine endpoint type for rate limiting
        endpoint_type = self._get_endpoint_type(request.url.path)
        
        # Check rate limits
        if not self.rate_limiter.is_allowed(client_ip, endpoint_type):
            self.security_logger.log_rate_limit_violation(
                client_ip, request.url.path, 
                self.rate_limiter.limits.get(endpoint_type, 100)
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded. The ghost is not pleased with your haste! 👻",
                    "retry_after": self.rate_limiter.block_duration * 60
                }
            )
        
        # Validate request size
        if hasattr(request, 'headers') and 'content-length' in request.headers:
            content_length = int(request.headers['content-length'])
            if content_length > 1024 * 1024:  # 1MB limit
                self.security_logger.log_input_validation_failure(
                    client_ip, 'REQUEST_SIZE', f'Request too large: {content_length} bytes'
                )
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"error": "Request too large. Even ghosts have limits! 👻"}
                )
        
        # Add security headers to response
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        
        # Add rate limit headers
        remaining = self.rate_limiter.get_remaining_requests(client_ip, endpoint_type)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.limits.get(endpoint_type, 100))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address"""
        # Check for forwarded headers (for reverse proxy setups)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if hasattr(request, 'client') and request.client:
            return request.client.host
        
        return 'unknown'
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determine endpoint type for rate limiting"""
        if '/execute' in path:
            return 'code_execution'
        elif '/ghost' in path or '/ai' in path:
            return 'ai_requests'
        else:
            return 'api_requests'


# Global instances
rate_limiter = RateLimiter()
security_logger = SecurityLogger()
input_validator = InputValidator()