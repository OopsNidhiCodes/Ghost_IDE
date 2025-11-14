"""
Authentication and authorization middleware for GhostIDE
"""

import jwt
import time
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = "ghost-ide-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer(auto_error=False)


class SessionManager:
    """Manage user sessions and authentication"""
    
    def __init__(self):
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(hours=2)  # 2 hour session timeout
    
    def create_session(self, session_id: str, client_ip: str) -> Dict[str, Any]:
        """Create a new session"""
        session_data = {
            'session_id': session_id,
            'client_ip': client_ip,
            'created_at': datetime.now(),
            'last_activity': datetime.now(),
            'request_count': 0,
            'is_authenticated': False
        }
        
        self.active_sessions[session_id] = session_data
        logger.info(f"Created new session: {session_id} from IP: {client_ip}")
        return session_data
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        
        # Check if session has expired
        if datetime.now() - session['last_activity'] > self.session_timeout:
            self.invalidate_session(session_id)
            return None
        
        return session
    
    def update_session_activity(self, session_id: str) -> bool:
        """Update session last activity"""
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['last_activity'] = datetime.now()
            self.active_sessions[session_id]['request_count'] += 1
            return True
        return False
    
    def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a session"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Invalidated session: {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            if now - session_data['last_activity'] > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            self.invalidate_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


class JWTManager:
    """JWT token management"""
    
    @staticmethod
    def create_token(session_id: str, client_ip: str) -> str:
        """Create JWT token"""
        payload = {
            'session_id': session_id,
            'client_ip': client_ip,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    
    @staticmethod
    def verify_token(token: str, client_ip: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Verify client IP matches
            if payload.get('client_ip') != client_ip:
                logger.warning(f"IP mismatch in token verification: {client_ip} vs {payload.get('client_ip')}")
                return None
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.info("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None


def generate_session_id(client_ip: str, user_agent: str = "") -> str:
    """Generate unique session ID"""
    timestamp = str(time.time())
    data = f"{client_ip}:{user_agent}:{timestamp}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    
    real_ip = request.headers.get('X-Real-IP')
    if real_ip:
        return real_ip
    
    if hasattr(request, 'client') and request.client:
        return request.client.host
    
    return 'unknown'


# Global session manager
session_manager = SessionManager()
jwt_manager = JWTManager()


async def get_current_session(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Get current session from request"""
    client_ip = get_client_ip(request)
    
    # Try to get session from JWT token first
    if credentials:
        token_payload = jwt_manager.verify_token(credentials.credentials, client_ip)
        if token_payload:
            session_id = token_payload['session_id']
            session = session_manager.get_session(session_id)
            if session:
                session_manager.update_session_activity(session_id)
                return session
    
    # Try to get session ID from headers
    session_id = request.headers.get('X-Session-ID')
    if session_id:
        session = session_manager.get_session(session_id)
        if session and session['client_ip'] == client_ip:
            session_manager.update_session_activity(session_id)
            return session
    
    # Create new session
    user_agent = request.headers.get('User-Agent', '')
    new_session_id = generate_session_id(client_ip, user_agent)
    return session_manager.create_session(new_session_id, client_ip)


async def require_valid_session(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """Require a valid session for protected endpoints"""
    session = await get_current_session(request, credentials)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. The ghost demands proper identification! 👻"
        )
    
    return session


def create_session_token(session_id: str, client_ip: str) -> str:
    """Create session token for client"""
    return jwt_manager.create_token(session_id, client_ip)