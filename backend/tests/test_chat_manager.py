"""
Unit tests for chat management service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.chat_manager import ChatManager, get_chat_manager


@pytest.fixture
def chat_manager():
    """Create a chat manager for testing"""
    return ChatManager()


class TestChatManager:
    """Test cases for ChatManager"""
    
    @pytest.mark.asyncio
    async def test_add_message(self, chat_manager):
        """Test adding a new chat message"""
        session_id = "test-session-id"
        content = "Hello, Ghost!"
        sender = "user"
        context = {"code": "print('hello')"}
        
        with patch.object(chat_manager.session_manager, 'validate_session') as mock_validate:
            mock_validate.return_value = True
            
            with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
                mock_session = AsyncMock()
                mock_db.return_value.__aenter__.return_value = mock_session
                
                # Mock database operations
                mock_db_message = MagicMock()
                mock_db_message.id = "test-message-id"
                mock_db_message.content = content
                mock_db_message.sender = sender
                mock_db_message.timestamp = datetime.utcnow()
                mock_db_message.context = context
                
                mock_session.add = AsyncMock()
                mock_session.commit = AsyncMock()
                mock_session.refresh = AsyncMock()
                
                with patch.object(chat_manager.session_manager, 'get_session') as mock_get_session:
                    mock_get_session.return_value = MagicMock()
                    
                    with patch.object(chat_manager, '_cleanup_old_messages') as mock_cleanup:
                        mock_cleanup.return_value = None
                        
                        message = await chat_manager.add_message(session_id, content, sender, context)
                        
                        assert message is not None
                        assert message.content == content
                        assert message.sender == sender
                        assert message.context == context
    
    @pytest.mark.asyncio
    async def test_add_message_invalid_session(self, chat_manager):
        """Test adding message to invalid session"""
        session_id = "invalid-session-id"
        
        with patch.object(chat_manager.session_manager, 'validate_session') as mock_validate:
            mock_validate.return_value = False
            
            message = await chat_manager.add_message(session_id, "Hello", "user")
            
            assert message is None
    
    @pytest.mark.asyncio
    async def test_get_session_messages(self, chat_manager):
        """Test getting messages for a session"""
        session_id = "test-session-id"
        
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock multiple messages
            mock_msg1 = MagicMock()
            mock_msg1.id = "msg1"
            mock_msg1.content = "Hello"
            mock_msg1.sender = "user"
            mock_msg1.timestamp = datetime.utcnow() - timedelta(minutes=5)
            mock_msg1.context = {}
            
            mock_msg2 = MagicMock()
            mock_msg2.id = "msg2"
            mock_msg2.content = "Greetings, mortal!"
            mock_msg2.sender = "ghost"
            mock_msg2.timestamp = datetime.utcnow()
            mock_msg2.context = {}
            
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = [mock_msg2, mock_msg1]  # Reversed order
            mock_session.execute.return_value = mock_result
            
            messages = await chat_manager.get_session_messages(session_id)
            
            assert len(messages) == 2
            # Should be in chronological order (oldest first)
            assert messages[0].content == "Hello"
            assert messages[1].content == "Greetings, mortal!"
    
    @pytest.mark.asyncio
    async def test_get_recent_messages(self, chat_manager):
        """Test getting recent messages"""
        session_id = "test-session-id"
        
        with patch.object(chat_manager, 'get_session_messages') as mock_get_messages:
            mock_messages = [MagicMock() for _ in range(5)]
            mock_get_messages.return_value = mock_messages
            
            recent_messages = await chat_manager.get_recent_messages(session_id, count=3)
            
            mock_get_messages.assert_called_once_with(session_id, limit=3)
            assert recent_messages == mock_messages
    
    @pytest.mark.asyncio
    async def test_get_message(self, chat_manager):
        """Test getting a specific message"""
        session_id = "test-session-id"
        message_id = "test-message-id"
        
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock message
            mock_db_message = MagicMock()
            mock_db_message.id = message_id
            mock_db_message.content = "Test message"
            mock_db_message.sender = "user"
            mock_db_message.timestamp = datetime.utcnow()
            mock_db_message.context = {}
            
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_message
            mock_session.execute.return_value = mock_result
            
            message = await chat_manager.get_message(session_id, message_id)
            
            assert message is not None
            assert message.id == message_id
            assert message.content == "Test message"
    
    @pytest.mark.asyncio
    async def test_delete_message(self, chat_manager):
        """Test deleting a message"""
        session_id = "test-session-id"
        message_id = "test-message-id"
        
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock existing message
            mock_db_message = MagicMock()
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = mock_db_message
            mock_session.execute.return_value = mock_result
            
            mock_session.delete = AsyncMock()
            mock_session.commit = AsyncMock()
            
            with patch.object(chat_manager.session_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value = MagicMock()
                
                success = await chat_manager.delete_message(session_id, message_id)
                
                assert success is True
    
    @pytest.mark.asyncio
    async def test_clear_session_history(self, chat_manager):
        """Test clearing all chat history"""
        session_id = "test-session-id"
        
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_session.execute = AsyncMock()
            mock_session.commit = AsyncMock()
            
            with patch.object(chat_manager.session_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value = MagicMock()
                
                success = await chat_manager.clear_session_history(session_id)
                
                assert success is True
    
    @pytest.mark.asyncio
    async def test_get_message_count(self, chat_manager):
        """Test getting message count"""
        session_id = "test-session-id"
        
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_result = AsyncMock()
            mock_result.scalar.return_value = 5
            mock_session.execute.return_value = mock_result
            
            count = await chat_manager.get_message_count(session_id)
            
            assert count == 5
    
    @pytest.mark.asyncio
    async def test_search_messages(self, chat_manager):
        """Test searching messages by content"""
        session_id = "test-session-id"
        query = "hello"
        sender = "user"
        
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock search results
            mock_message = MagicMock()
            mock_message.id = "msg1"
            mock_message.content = "Hello world"
            mock_message.sender = "user"
            mock_message.timestamp = datetime.utcnow()
            mock_message.context = {}
            
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = [mock_message]
            mock_session.execute.return_value = mock_result
            
            messages = await chat_manager.search_messages(session_id, query, sender)
            
            assert len(messages) == 1
            assert messages[0].content == "Hello world"
    
    @pytest.mark.asyncio
    async def test_get_conversation_context(self, chat_manager):
        """Test getting conversation context"""
        session_id = "test-session-id"
        
        # Mock recent messages
        mock_messages = []
        for i in range(3):
            msg = MagicMock()
            msg.timestamp = datetime.utcnow() - timedelta(minutes=i)
            msg.sender = "user" if i % 2 == 0 else "ghost"
            msg.content = f"Message {i}"
            mock_messages.append(msg)
        
        with patch.object(chat_manager, 'get_recent_messages') as mock_get_recent:
            mock_get_recent.return_value = mock_messages
            
            context = await chat_manager.get_conversation_context(session_id, max_messages=3)
            
            assert "user: Message 0" in context
            assert "ghost: Message 1" in context
            assert "user: Message 2" in context
    
    @pytest.mark.asyncio
    async def test_add_ghost_response(self, chat_manager):
        """Test adding a ghost response"""
        session_id = "test-session-id"
        response = "Boo! I'm here to help!"
        
        with patch.object(chat_manager, 'add_message') as mock_add_message:
            mock_message = MagicMock()
            mock_add_message.return_value = mock_message
            
            result = await chat_manager.add_ghost_response(session_id, response)
            
            mock_add_message.assert_called_once_with(session_id, response, "ghost", None)
            assert result == mock_message
    
    @pytest.mark.asyncio
    async def test_add_user_message(self, chat_manager):
        """Test adding a user message"""
        session_id = "test-session-id"
        message = "Help me with my code"
        
        with patch.object(chat_manager, 'add_message') as mock_add_message:
            mock_message = MagicMock()
            mock_add_message.return_value = mock_message
            
            result = await chat_manager.add_user_message(session_id, message)
            
            mock_add_message.assert_called_once_with(session_id, message, "user", None)
            assert result == mock_message
    
    @pytest.mark.asyncio
    async def test_cleanup_old_messages(self, chat_manager):
        """Test cleanup of old messages when limit exceeded"""
        session_id = "test-session-id"
        
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock message count exceeding limit
            mock_count_result = AsyncMock()
            mock_count_result.scalar.return_value = chat_manager.max_messages_per_session + 10
            
            # Mock old message IDs
            mock_ids_result = AsyncMock()
            mock_ids_result.scalars.return_value.all.return_value = ["old1", "old2", "old3"]
            
            mock_session.execute.side_effect = [mock_count_result, mock_ids_result, AsyncMock()]
            
            await chat_manager._cleanup_old_messages(session_id, mock_session)
            
            # Should have executed delete query
            assert mock_session.execute.call_count == 3
    
    @pytest.mark.asyncio
    async def test_cleanup_old_messages_globally(self, chat_manager):
        """Test global cleanup of old messages"""
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_session.execute = AsyncMock()
            mock_session.commit = AsyncMock()
            
            await chat_manager.cleanup_old_messages_globally()
            
            # Should have executed delete query and committed
            mock_session.execute.assert_called_once()
            mock_session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_stats(self, chat_manager):
        """Test getting session statistics"""
        session_id = "test-session-id"
        
        with patch('app.services.chat_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock statistics queries
            mock_results = [
                AsyncMock(),  # total count
                AsyncMock(),  # user count
                AsyncMock(),  # ghost count
                AsyncMock(),  # first message
                AsyncMock()   # last message
            ]
            
            mock_results[0].scalar.return_value = 10  # total
            mock_results[1].scalar.return_value = 6   # user
            mock_results[2].scalar.return_value = 4   # ghost
            mock_results[3].scalar.return_value = datetime.utcnow() - timedelta(hours=1)  # first
            mock_results[4].scalar.return_value = datetime.utcnow()  # last
            
            mock_session.execute.side_effect = mock_results
            
            stats = await chat_manager.get_session_stats(session_id)
            
            assert stats["total_messages"] == 10
            assert stats["user_messages"] == 6
            assert stats["ghost_messages"] == 4
            assert stats["first_message_at"] is not None
            assert stats["last_message_at"] is not None
            assert stats["conversation_duration"] is not None


class TestChatManagerIntegration:
    """Integration tests for chat manager"""
    
    def test_get_chat_manager_singleton(self):
        """Test that get_chat_manager returns singleton"""
        manager1 = get_chat_manager()
        manager2 = get_chat_manager()
        
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_message_lifecycle(self, chat_manager):
        """Test complete message lifecycle"""
        session_id = "test-session-id"
        
        with patch.object(chat_manager.session_manager, 'validate_session') as mock_validate, \
             patch('app.services.chat_manager.AsyncSessionLocal') as mock_db, \
             patch.object(chat_manager.session_manager, 'get_session') as mock_get_session:
            
            mock_validate.return_value = True
            mock_get_session.return_value = MagicMock()
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock database operations
            mock_db_message = MagicMock()
            mock_db_message.id = "test-message-id"
            mock_db_message.content = "Hello"
            mock_db_message.sender = "user"
            mock_db_message.timestamp = datetime.utcnow()
            mock_db_message.context = {}
            
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session.delete = AsyncMock()
            
            with patch.object(chat_manager, '_cleanup_old_messages') as mock_cleanup:
                mock_cleanup.return_value = None
                
                # Add message
                message = await chat_manager.add_message(session_id, "Hello", "user")
                assert message is not None
                
                # Delete message
                mock_result = AsyncMock()
                mock_result.scalar_one_or_none.return_value = mock_db_message
                mock_session.execute.return_value = mock_result
                
                success = await chat_manager.delete_message(session_id, message.id)
                assert success is True


if __name__ == "__main__":
    pytest.main([__file__])