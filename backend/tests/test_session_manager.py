"""
Unit tests for session management service
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.session_manager import SessionManager, get_session_manager
from app.models.schemas import UserSessionCreate, UserSessionUpdate, UserPreferences, LanguageType


@pytest.fixture
def session_manager():
    """Create a session manager for testing"""
    return SessionManager("redis://localhost:6379/1")  # Use test database


@pytest.fixture
def sample_session_data():
    """Sample session creation data"""
    return UserSessionCreate(
        current_language=LanguageType.PYTHON,
        preferences=UserPreferences(
            theme="ghost-dark",
            font_size=14,
            auto_save=True
        )
    )


class TestSessionManager:
    """Test cases for SessionManager"""
    
    @pytest.mark.asyncio
    async def test_create_session(self, session_manager, sample_session_data):
        """Test creating a new session"""
        with patch('app.services.session_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock database operations
            mock_db_session = MagicMock()
            mock_db_session.id = "test-session-id"
            mock_db_session.created_at = datetime.utcnow()
            mock_db_session.last_activity = datetime.utcnow()
            
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            # Mock Redis operations
            with patch.object(session_manager, 'get_redis') as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis.return_value = mock_redis_client
                
                session = await session_manager.create_session(sample_session_data)
                
                assert session is not None
                assert session.current_language == LanguageType.PYTHON
                assert session.preferences.theme == "ghost-dark"
                assert len(session.files) == 0
                assert len(session.chat_history) == 0
    
    @pytest.mark.asyncio
    async def test_get_session_from_redis(self, session_manager):
        """Test getting session from Redis cache"""
        session_id = "test-session-id"
        
        # Mock Redis data
        redis_data = {
            "id": session_id,
            "current_language": "python",
            "preferences": {"theme": "ghost-dark", "font_size": 14, "auto_save": True},
            "files": [],
            "chat_history": [],
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        with patch.object(session_manager, 'get_redis') as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.get.return_value = '{"id": "test-session-id", "current_language": "python", "preferences": {"theme": "ghost-dark", "font_size": 14, "auto_save": true}, "files": [], "chat_history": [], "created_at": "2023-01-01T00:00:00", "last_activity": "2023-01-01T00:00:00"}'
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.sadd = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            session = await session_manager.get_session(session_id)
            
            assert session is not None
            assert session.id == session_id
            assert session.current_language == LanguageType.PYTHON
    
    @pytest.mark.asyncio
    async def test_get_session_fallback_to_postgres(self, session_manager):
        """Test fallback to PostgreSQL when session not in Redis"""
        session_id = "test-session-id"
        
        with patch.object(session_manager, 'get_redis') as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.get.return_value = None  # Not in Redis
            mock_redis.return_value = mock_redis_client
            
            with patch('app.services.session_manager.AsyncSessionLocal') as mock_db:
                mock_session = AsyncMock()
                mock_db.return_value.__aenter__.return_value = mock_session
                
                # Mock database query result
                mock_result = AsyncMock()
                mock_db_session = MagicMock()
                mock_db_session.id = session_id
                mock_db_session.current_language = "python"
                mock_db_session.preferences = {"theme": "ghost-dark", "font_size": 14, "auto_save": True}
                mock_db_session.files = []
                mock_db_session.chat_messages = []
                mock_db_session.created_at = datetime.utcnow()
                mock_db_session.last_activity = datetime.utcnow()
                
                mock_result.scalar_one_or_none.return_value = mock_db_session
                mock_session.execute.return_value = mock_result
                mock_session.commit = AsyncMock()
                
                session = await session_manager.get_session(session_id)
                
                assert session is not None
                assert session.id == session_id
    
    @pytest.mark.asyncio
    async def test_update_session(self, session_manager):
        """Test updating a session"""
        session_id = "test-session-id"
        
        # Mock existing session
        with patch.object(session_manager, 'get_session') as mock_get:
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.current_language = LanguageType.PYTHON
            mock_session.preferences = UserPreferences()
            mock_session.last_activity = datetime.utcnow()
            mock_get.return_value = mock_session
            
            with patch('app.services.session_manager.AsyncSessionLocal') as mock_db:
                mock_db_session = AsyncMock()
                mock_db.return_value.__aenter__.return_value = mock_db_session
                mock_db_session.execute = AsyncMock()
                mock_db_session.commit = AsyncMock()
                
                with patch.object(session_manager, '_store_active_session') as mock_store:
                    update_data = UserSessionUpdate(current_language=LanguageType.JAVASCRIPT)
                    
                    updated_session = await session_manager.update_session(session_id, update_data)
                    
                    assert updated_session is not None
                    assert updated_session.current_language == LanguageType.JAVASCRIPT
    
    @pytest.mark.asyncio
    async def test_delete_session(self, session_manager):
        """Test deleting a session"""
        session_id = "test-session-id"
        
        with patch.object(session_manager, 'get_redis') as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.delete = AsyncMock()
            mock_redis_client.srem = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            with patch('app.services.session_manager.AsyncSessionLocal') as mock_db:
                mock_session = AsyncMock()
                mock_db.return_value.__aenter__.return_value = mock_session
                
                # Mock database operations
                mock_result = AsyncMock()
                mock_db_session = MagicMock()
                mock_result.scalar_one_or_none.return_value = mock_db_session
                mock_session.execute.return_value = mock_result
                mock_session.delete = AsyncMock()
                mock_session.commit = AsyncMock()
                
                success = await session_manager.delete_session(session_id)
                
                assert success is True
    
    @pytest.mark.asyncio
    async def test_validate_session(self, session_manager):
        """Test session validation"""
        session_id = "test-session-id"
        
        with patch.object(session_manager, 'get_session') as mock_get:
            mock_get.return_value = MagicMock()  # Session exists
            
            is_valid = await session_manager.validate_session(session_id)
            assert is_valid is True
            
            mock_get.return_value = None  # Session doesn't exist
            is_valid = await session_manager.validate_session(session_id)
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, session_manager):
        """Test cleanup of expired sessions"""
        with patch.object(session_manager, 'get_redis') as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.smembers.return_value = {"session1", "session2", "session3"}
            mock_redis_client.exists.side_effect = [True, False, True]  # session2 expired
            mock_redis_client.srem = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            with patch('app.services.session_manager.AsyncSessionLocal') as mock_db:
                mock_session = AsyncMock()
                mock_db.return_value.__aenter__.return_value = mock_session
                mock_session.execute = AsyncMock()
                mock_session.commit = AsyncMock()
                
                await session_manager.cleanup_expired_sessions()
                
                # Should remove expired session from active set
                mock_redis_client.srem.assert_called_with(
                    session_manager._active_sessions_key(), "session2"
                )
    
    @pytest.mark.asyncio
    async def test_get_active_sessions(self, session_manager):
        """Test getting active sessions"""
        with patch.object(session_manager, 'get_redis') as mock_redis:
            mock_redis_client = AsyncMock()
            mock_redis_client.smembers.return_value = {"session1", "session2"}
            mock_redis.return_value = mock_redis_client
            
            active_sessions = await session_manager.get_active_sessions()
            
            assert "session1" in active_sessions
            assert "session2" in active_sessions
    
    @pytest.mark.asyncio
    async def test_get_session_security_info(self, session_manager):
        """Test getting session security information"""
        session_id = "test-session-id"
        
        with patch.object(session_manager, 'get_session') as mock_get:
            mock_session = MagicMock()
            mock_session.id = session_id
            mock_session.created_at = datetime.utcnow()
            mock_session.last_activity = datetime.utcnow()
            mock_session.files = []
            mock_session.chat_history = []
            mock_get.return_value = mock_session
            
            with patch.object(session_manager, 'get_redis') as mock_redis:
                mock_redis_client = AsyncMock()
                mock_redis_client.ttl.return_value = 3600  # 1 hour remaining
                mock_redis.return_value = mock_redis_client
                
                security_info = await session_manager.get_session_security_info(session_id)
                
                assert security_info is not None
                assert security_info["session_id"] == session_id
                assert security_info["is_active"] is True
                assert security_info["expires_in_seconds"] == 3600


class TestSessionManagerIntegration:
    """Integration tests for session manager"""
    
    def test_get_session_manager_singleton(self):
        """Test that get_session_manager returns singleton"""
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_session_lifecycle(self, session_manager, sample_session_data):
        """Test complete session lifecycle"""
        with patch('app.services.session_manager.AsyncSessionLocal') as mock_db, \
             patch.object(session_manager, 'get_redis') as mock_redis:
            
            # Setup mocks
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock database session
            mock_db_session = MagicMock()
            mock_db_session.id = "test-session-id"
            mock_db_session.created_at = datetime.utcnow()
            mock_db_session.last_activity = datetime.utcnow()
            
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session.delete = AsyncMock()
            
            # Create session
            session = await session_manager.create_session(sample_session_data)
            assert session is not None
            
            # Update session
            update_data = UserSessionUpdate(current_language=LanguageType.JAVASCRIPT)
            with patch.object(session_manager, 'get_session') as mock_get:
                mock_get.return_value = session
                updated_session = await session_manager.update_session(session.id, update_data)
                assert updated_session.current_language == LanguageType.JAVASCRIPT
            
            # Delete session
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_session
            mock_session.execute.return_value = mock_result
            
            success = await session_manager.delete_session(session.id)
            assert success is True


@pytest.mark.asyncio
async def test_session_manager_error_handling():
    """Test error handling in session manager"""
    manager = SessionManager("redis://invalid:6379/0")
    
    # Test Redis connection error handling
    with patch.object(manager, 'get_redis') as mock_redis:
        mock_redis.side_effect = Exception("Redis connection failed")
        
        # Should handle Redis errors gracefully
        with pytest.raises(Exception):
            await manager.get_active_sessions()
    
    await manager.close()


if __name__ == "__main__":
    pytest.main([__file__])