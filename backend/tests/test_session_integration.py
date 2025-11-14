"""
Integration tests for session management system
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.session_manager import SessionManager
from app.services.file_manager import FileManager
from app.services.chat_manager import ChatManager
from app.services.cleanup_service import CleanupService
from app.models.schemas import (
    UserSessionCreate, UserSessionUpdate, UserPreferences, LanguageType,
    CodeFileCreate, CodeFileUpdate
)


@pytest.fixture
async def session_system():
    """Create integrated session management system for testing"""
    session_manager = SessionManager("redis://localhost:6379/1")
    file_manager = FileManager()
    chat_manager = ChatManager()
    cleanup_service = CleanupService()
    
    # Override managers in file and chat managers
    file_manager.session_manager = session_manager
    chat_manager.session_manager = session_manager
    cleanup_service.session_manager = session_manager
    cleanup_service.chat_manager = chat_manager
    
    yield {
        'session_manager': session_manager,
        'file_manager': file_manager,
        'chat_manager': chat_manager,
        'cleanup_service': cleanup_service
    }
    
    await session_manager.close()


@pytest.fixture
def sample_data():
    """Sample data for testing"""
    return {
        'session_data': UserSessionCreate(
            current_language=LanguageType.PYTHON,
            preferences=UserPreferences(
                theme="ghost-dark",
                font_size=14,
                auto_save=True
            )
        ),
        'file_data': CodeFileCreate(
            name="main.py",
            content="print('Hello, Ghost World!')",
            language=LanguageType.PYTHON
        )
    }


class TestSessionIntegration:
    """Integration tests for session management system"""
    
    @pytest.mark.asyncio
    async def test_complete_session_workflow(self, session_system, sample_data):
        """Test complete session workflow with files and chat"""
        session_manager = session_system['session_manager']
        file_manager = session_system['file_manager']
        chat_manager = session_system['chat_manager']
        
        with patch('app.services.session_manager.AsyncSessionLocal') as mock_db, \
             patch.object(session_manager, 'get_redis') as mock_redis:
            
            # Setup mocks
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock database operations
            mock_db_session = MagicMock()
            mock_db_session.id = "test-session-id"
            mock_db_session.created_at = datetime.utcnow()
            mock_db_session.last_activity = datetime.utcnow()
            
            mock_db_file = MagicMock()
            mock_db_file.id = "test-file-id"
            mock_db_file.name = sample_data['file_data'].name
            mock_db_file.content = sample_data['file_data'].content
            mock_db_file.language = sample_data['file_data'].language.value
            mock_db_file.last_modified = datetime.utcnow()
            
            mock_db_message = MagicMock()
            mock_db_message.id = "test-message-id"
            mock_db_message.content = "Hello, Ghost!"
            mock_db_message.sender = "user"
            mock_db_message.timestamp = datetime.utcnow()
            mock_db_message.context = {}
            
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session.delete = AsyncMock()
            
            # 1. Create session
            session = await session_manager.create_session(sample_data['session_data'])
            assert session is not None
            assert session.current_language == LanguageType.PYTHON
            
            # 2. Add file to session
            with patch.object(file_manager.session_manager, 'validate_session', return_value=True), \
                 patch.object(file_manager.session_manager, 'get_session', return_value=session):
                
                file = await file_manager.create_file(session.id, sample_data['file_data'])
                assert file is not None
                assert file.name == "main.py"
            
            # 3. Add chat message
            with patch.object(chat_manager.session_manager, 'validate_session', return_value=True), \
                 patch.object(chat_manager.session_manager, 'get_session', return_value=session), \
                 patch.object(chat_manager, '_cleanup_old_messages', return_value=None):
                
                message = await chat_manager.add_user_message(session.id, "Hello, Ghost!")
                assert message is not None
                assert message.content == "Hello, Ghost!"
            
            # 4. Update session
            update_data = UserSessionUpdate(current_language=LanguageType.JAVASCRIPT)
            with patch.object(session_manager, 'get_session', return_value=session), \
                 patch.object(session_manager, '_store_active_session', return_value=None):
                
                updated_session = await session_manager.update_session(session.id, update_data)
                assert updated_session is not None
                assert updated_session.current_language == LanguageType.JAVASCRIPT
            
            # 5. Validate session
            with patch.object(session_manager, 'get_session', return_value=session):
                is_valid = await session_manager.validate_session(session.id)
                assert is_valid is True
            
            # 6. Get security info
            with patch.object(session_manager, 'get_session', return_value=session):
                mock_redis_client.ttl.return_value = 3600
                security_info = await session_manager.get_session_security_info(session.id)
                assert security_info is not None
                assert security_info['session_id'] == session.id
            
            # 7. Delete session
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_session
            mock_session.execute.return_value = mock_result
            
            success = await session_manager.delete_session(session.id)
            assert success is True
    
    @pytest.mark.asyncio
    async def test_session_restoration(self, session_system, sample_data):
        """Test session restoration from PostgreSQL to Redis"""
        session_manager = session_system['session_manager']
        
        with patch('app.services.session_manager.AsyncSessionLocal') as mock_db, \
             patch.object(session_manager, 'get_redis') as mock_redis:
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_redis_client = AsyncMock()
            mock_redis_client.get.return_value = None  # Not in Redis
            mock_redis_client.setex = AsyncMock()
            mock_redis_client.sadd = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock PostgreSQL data
            mock_db_session = MagicMock()
            mock_db_session.id = "restored-session-id"
            mock_db_session.current_language = "python"
            mock_db_session.preferences = {"theme": "ghost-dark", "font_size": 14, "auto_save": True}
            mock_db_session.files = []
            mock_db_session.chat_messages = []
            mock_db_session.created_at = datetime.utcnow()
            mock_db_session.last_activity = datetime.utcnow()
            
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_session
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()
            
            # Restore session
            restored_session = await session_manager.restore_session("restored-session-id")
            
            assert restored_session is not None
            assert restored_session.id == "restored-session-id"
            assert restored_session.current_language == LanguageType.PYTHON
            
            # Should have stored in Redis
            mock_redis_client.setex.assert_called_once()
            mock_redis_client.sadd.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_file_operations_with_session_updates(self, session_system, sample_data):
        """Test file operations update session activity"""
        session_manager = session_system['session_manager']
        file_manager = session_system['file_manager']
        
        session_id = "test-session-id"
        
        with patch('app.services.file_manager.AsyncSessionLocal') as mock_db, \
             patch.object(file_manager.session_manager, 'validate_session', return_value=True), \
             patch.object(file_manager.session_manager, 'get_session') as mock_get_session:
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_db_file = MagicMock()
            mock_db_file.id = "test-file-id"
            mock_db_file.name = sample_data['file_data'].name
            mock_db_file.content = sample_data['file_data'].content
            mock_db_file.language = sample_data['file_data'].language.value
            mock_db_file.last_modified = datetime.utcnow()
            
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            mock_get_session.return_value = MagicMock()
            
            # Create file should update session activity
            file = await file_manager.create_file(session_id, sample_data['file_data'])
            
            assert file is not None
            # Verify session activity was updated
            mock_get_session.assert_called_with(session_id, update_activity=True)
    
    @pytest.mark.asyncio
    async def test_chat_operations_with_session_updates(self, session_system):
        """Test chat operations update session activity"""
        session_manager = session_system['session_manager']
        chat_manager = session_system['chat_manager']
        
        session_id = "test-session-id"
        
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db, \
             patch.object(chat_manager.session_manager, 'validate_session', return_value=True), \
             patch.object(chat_manager.session_manager, 'get_session') as mock_get_session, \
             patch.object(chat_manager, '_cleanup_old_messages', return_value=None):
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_db_message = MagicMock()
            mock_db_message.id = "test-message-id"
            mock_db_message.content = "Test message"
            mock_db_message.sender = "user"
            mock_db_message.timestamp = datetime.utcnow()
            mock_db_message.context = {}
            
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            mock_get_session.return_value = MagicMock()
            
            # Add message should update session activity
            message = await chat_manager.add_user_message(session_id, "Test message")
            
            assert message is not None
            # Verify session activity was updated
            mock_get_session.assert_called_with(session_id, update_activity=True)
    
    @pytest.mark.asyncio
    async def test_cleanup_service_integration(self, session_system):
        """Test cleanup service with session and chat managers"""
        session_manager = session_system['session_manager']
        chat_manager = session_system['chat_manager']
        cleanup_service = session_system['cleanup_service']
        
        with patch.object(session_manager, 'cleanup_expired_sessions') as mock_session_cleanup, \
             patch.object(session_manager, 'get_active_sessions') as mock_get_active, \
             patch.object(chat_manager, 'cleanup_old_messages_globally') as mock_chat_cleanup:
            
            mock_session_cleanup.return_value = None
            mock_get_active.return_value = ["session1", "session2"]
            mock_chat_cleanup.return_value = None
            
            # Run cleanup
            await cleanup_service.run_cleanup()
            
            # Verify all cleanup methods were called
            mock_session_cleanup.assert_called_once()
            mock_get_active.assert_called_once()
            mock_chat_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self, session_system, sample_data):
        """Test concurrent operations on the same session"""
        session_manager = session_system['session_manager']
        file_manager = session_system['file_manager']
        chat_manager = session_system['chat_manager']
        
        session_id = "concurrent-session-id"
        
        with patch('app.services.session_manager.AsyncSessionLocal') as mock_db, \
             patch.object(session_manager, 'get_redis') as mock_redis, \
             patch('app.services.file_manager.AsyncSessionLocal') as mock_file_db, \
             patch('app.services.chat_manager.AsyncSessionLocal') as mock_chat_db:
            
            # Setup mocks for all services
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            mock_file_db.return_value.__aenter__.return_value = mock_session
            mock_chat_db.return_value.__aenter__.return_value = mock_session
            
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            mock_session.execute = AsyncMock()
            
            # Mock session validation and updates
            with patch.object(file_manager.session_manager, 'validate_session', return_value=True), \
                 patch.object(file_manager.session_manager, 'get_session', return_value=MagicMock()), \
                 patch.object(chat_manager.session_manager, 'validate_session', return_value=True), \
                 patch.object(chat_manager.session_manager, 'get_session', return_value=MagicMock()), \
                 patch.object(chat_manager, '_cleanup_old_messages', return_value=None):
                
                # Run concurrent operations
                tasks = [
                    file_manager.create_file(session_id, sample_data['file_data']),
                    chat_manager.add_user_message(session_id, "Concurrent message 1"),
                    chat_manager.add_user_message(session_id, "Concurrent message 2"),
                ]
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # All operations should succeed
                assert len(results) == 3
                for result in results:
                    assert not isinstance(result, Exception)
    
    @pytest.mark.asyncio
    async def test_error_propagation(self, session_system, sample_data):
        """Test error propagation through the system"""
        session_manager = session_system['session_manager']
        file_manager = session_system['file_manager']
        
        session_id = "error-session-id"
        
        # Test file creation with invalid session
        with patch.object(file_manager.session_manager, 'validate_session', return_value=False):
            file = await file_manager.create_file(session_id, sample_data['file_data'])
            assert file is None
        
        # Test session operations with database errors
        with patch('app.services.session_manager.AsyncSessionLocal') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception):
                await session_manager.create_session(sample_data['session_data'])


class TestSessionPersistence:
    """Test session persistence across Redis and PostgreSQL"""
    
    @pytest.mark.asyncio
    async def test_redis_postgresql_consistency(self, session_system, sample_data):
        """Test consistency between Redis and PostgreSQL storage"""
        session_manager = session_system['session_manager']
        
        with patch('app.services.session_manager.AsyncSessionLocal') as mock_db, \
             patch.object(session_manager, 'get_redis') as mock_redis:
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_redis_client = AsyncMock()
            mock_redis.return_value = mock_redis_client
            
            # Mock database session
            mock_db_session = MagicMock()
            mock_db_session.id = "consistency-test-id"
            mock_db_session.created_at = datetime.utcnow()
            mock_db_session.last_activity = datetime.utcnow()
            
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            # Create session (should be stored in both Redis and PostgreSQL)
            session = await session_manager.create_session(sample_data['session_data'])
            
            assert session is not None
            
            # Verify Redis storage was called
            mock_redis_client.setex.assert_called_once()
            mock_redis_client.sadd.assert_called_once()
            
            # Verify PostgreSQL storage was called
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])