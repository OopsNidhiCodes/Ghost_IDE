"""
Unit tests for file management service
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock

from app.services.file_manager import FileManager, get_file_manager
from app.models.schemas import CodeFileCreate, CodeFileUpdate, LanguageType


@pytest.fixture
def file_manager():
    """Create a file manager for testing"""
    return FileManager()


@pytest.fixture
def sample_file_data():
    """Sample file creation data"""
    return CodeFileCreate(
        name="test.py",
        content="print('Hello, Ghost!')",
        language=LanguageType.PYTHON
    )


class TestFileManager:
    """Test cases for FileManager"""
    
    @pytest.mark.asyncio
    async def test_create_file(self, file_manager, sample_file_data):
        """Test creating a new file"""
        session_id = "test-session-id"
        
        with patch.object(file_manager.session_manager, 'validate_session') as mock_validate:
            mock_validate.return_value = True
            
            with patch('app.services.file_manager.AsyncSessionLocal') as mock_db:
                mock_session = AsyncMock()
                mock_db.return_value.__aenter__.return_value = mock_session
                
                # Mock database operations
                mock_db_file = MagicMock()
                mock_db_file.id = "test-file-id"
                mock_db_file.name = sample_file_data.name
                mock_db_file.content = sample_file_data.content
                mock_db_file.language = sample_file_data.language.value
                mock_db_file.last_modified = datetime.utcnow()
                
                mock_session.add = AsyncMock()
                mock_session.commit = AsyncMock()
                mock_session.refresh = AsyncMock()
                
                with patch.object(file_manager.session_manager, 'get_session') as mock_get_session:
                    mock_get_session.return_value = MagicMock()
                    
                    file = await file_manager.create_file(session_id, sample_file_data)
                    
                    assert file is not None
                    assert file.name == sample_file_data.name
                    assert file.content == sample_file_data.content
                    assert file.language == sample_file_data.language
    
    @pytest.mark.asyncio
    async def test_create_file_invalid_session(self, file_manager, sample_file_data):
        """Test creating file with invalid session"""
        session_id = "invalid-session-id"
        
        with patch.object(file_manager.session_manager, 'validate_session') as mock_validate:
            mock_validate.return_value = False
            
            file = await file_manager.create_file(session_id, sample_file_data)
            
            assert file is None
    
    @pytest.mark.asyncio
    async def test_get_file(self, file_manager):
        """Test getting a specific file"""
        session_id = "test-session-id"
        file_id = "test-file-id"
        
        with patch('app.services.file_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock database query result
            mock_result = AsyncMock()
            mock_db_file = MagicMock()
            mock_db_file.id = file_id
            mock_db_file.name = "test.py"
            mock_db_file.content = "print('Hello')"
            mock_db_file.language = "python"
            mock_db_file.last_modified = datetime.utcnow()
            
            mock_result.scalar_one_or_none.return_value = mock_db_file
            mock_session.execute.return_value = mock_result
            
            file = await file_manager.get_file(session_id, file_id)
            
            assert file is not None
            assert file.id == file_id
            assert file.name == "test.py"
    
    @pytest.mark.asyncio
    async def test_get_file_not_found(self, file_manager):
        """Test getting non-existent file"""
        session_id = "test-session-id"
        file_id = "non-existent-file-id"
        
        with patch('app.services.file_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none.return_value = None
            mock_session.execute.return_value = mock_result
            
            file = await file_manager.get_file(session_id, file_id)
            
            assert file is None
    
    @pytest.mark.asyncio
    async def test_get_session_files(self, file_manager):
        """Test getting all files in a session"""
        session_id = "test-session-id"
        
        with patch('app.services.file_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock multiple files
            mock_file1 = MagicMock()
            mock_file1.id = "file1"
            mock_file1.name = "test1.py"
            mock_file1.content = "print('1')"
            mock_file1.language = "python"
            mock_file1.last_modified = datetime.utcnow()
            
            mock_file2 = MagicMock()
            mock_file2.id = "file2"
            mock_file2.name = "test2.js"
            mock_file2.content = "console.log('2')"
            mock_file2.language = "javascript"
            mock_file2.last_modified = datetime.utcnow()
            
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = [mock_file1, mock_file2]
            mock_session.execute.return_value = mock_result
            
            files = await file_manager.get_session_files(session_id)
            
            assert len(files) == 2
            assert files[0].name == "test1.py"
            assert files[1].name == "test2.js"
    
    @pytest.mark.asyncio
    async def test_update_file(self, file_manager):
        """Test updating a file"""
        session_id = "test-session-id"
        file_id = "test-file-id"
        
        with patch('app.services.file_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock existing file
            mock_result1 = AsyncMock()
            mock_db_file = MagicMock()
            mock_db_file.id = file_id
            mock_result1.scalar_one_or_none.return_value = mock_db_file
            
            # Mock updated file
            mock_result2 = AsyncMock()
            mock_updated_file = MagicMock()
            mock_updated_file.id = file_id
            mock_updated_file.name = "updated.py"
            mock_updated_file.content = "print('Updated')"
            mock_updated_file.language = "python"
            mock_updated_file.last_modified = datetime.utcnow()
            mock_result2.scalar_one.return_value = mock_updated_file
            
            mock_session.execute.side_effect = [mock_result1, AsyncMock(), mock_result2]
            mock_session.commit = AsyncMock()
            
            with patch.object(file_manager.session_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value = MagicMock()
                
                update_data = CodeFileUpdate(name="updated.py", content="print('Updated')")
                file = await file_manager.update_file(session_id, file_id, update_data)
                
                assert file is not None
                assert file.name == "updated.py"
                assert file.content == "print('Updated')"
    
    @pytest.mark.asyncio
    async def test_delete_file(self, file_manager):
        """Test deleting a file"""
        session_id = "test-session-id"
        file_id = "test-file-id"
        
        with patch('app.services.file_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock existing file
            mock_result = AsyncMock()
            mock_db_file = MagicMock()
            mock_result.scalar_one_or_none.return_value = mock_db_file
            mock_session.execute.return_value = mock_result
            
            mock_session.delete = AsyncMock()
            mock_session.commit = AsyncMock()
            
            with patch.object(file_manager.session_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value = MagicMock()
                
                success = await file_manager.delete_file(session_id, file_id)
                
                assert success is True
    
    @pytest.mark.asyncio
    async def test_save_file_with_hook(self, file_manager):
        """Test saving a file and triggering hooks"""
        session_id = "test-session-id"
        file_id = "test-file-id"
        
        with patch('app.services.file_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock existing file
            mock_result = AsyncMock()
            mock_db_file = MagicMock()
            mock_db_file.id = file_id
            mock_db_file.name = "test.py"
            mock_db_file.content = "print('Hello')"
            mock_db_file.language = "python"
            mock_db_file.last_modified = datetime.utcnow()
            mock_result.scalar_one_or_none.return_value = mock_db_file
            mock_session.execute.return_value = mock_result
            mock_session.commit = AsyncMock()
            
            with patch.object(file_manager.session_manager, 'get_session') as mock_get_session:
                mock_get_session.return_value = MagicMock()
                
                with patch('app.services.file_manager.get_hook_manager') as mock_get_hook:
                    mock_hook_manager = AsyncMock()
                    mock_hook_manager.on_save_hook = AsyncMock()
                    mock_get_hook.return_value = mock_hook_manager
                    
                    file = await file_manager.save_file(session_id, file_id)
                    
                    assert file is not None
                    # Verify hook was called
                    mock_hook_manager.on_save_hook.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_duplicate_file(self, file_manager):
        """Test duplicating a file"""
        session_id = "test-session-id"
        file_id = "test-file-id"
        new_name = "duplicate.py"
        
        # Mock getting original file
        with patch.object(file_manager, 'get_file') as mock_get_file:
            mock_original_file = MagicMock()
            mock_original_file.name = "original.py"
            mock_original_file.content = "print('Original')"
            mock_original_file.language = LanguageType.PYTHON
            mock_get_file.return_value = mock_original_file
            
            # Mock creating duplicate
            with patch.object(file_manager, 'create_file') as mock_create_file:
                mock_duplicate_file = MagicMock()
                mock_duplicate_file.name = new_name
                mock_create_file.return_value = mock_duplicate_file
                
                duplicate = await file_manager.duplicate_file(session_id, file_id, new_name)
                
                assert duplicate is not None
                assert duplicate.name == new_name
    
    @pytest.mark.asyncio
    async def test_search_files(self, file_manager):
        """Test searching files by content"""
        session_id = "test-session-id"
        query = "hello"
        
        with patch('app.services.file_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock search results
            mock_file = MagicMock()
            mock_file.id = "file1"
            mock_file.name = "hello.py"
            mock_file.content = "print('Hello World')"
            mock_file.language = "python"
            mock_file.last_modified = datetime.utcnow()
            
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = [mock_file]
            mock_session.execute.return_value = mock_result
            
            files = await file_manager.search_files(session_id, query)
            
            assert len(files) == 1
            assert files[0].name == "hello.py"
    
    @pytest.mark.asyncio
    async def test_get_file_count(self, file_manager):
        """Test getting file count for a session"""
        session_id = "test-session-id"
        
        with patch('app.services.file_manager.AsyncSessionLocal') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock 3 files
            mock_files = [MagicMock(), MagicMock(), MagicMock()]
            mock_result = AsyncMock()
            mock_result.scalars.return_value.all.return_value = mock_files
            mock_session.execute.return_value = mock_result
            
            count = await file_manager.get_file_count(session_id)
            
            assert count == 3


class TestFileManagerIntegration:
    """Integration tests for file manager"""
    
    def test_get_file_manager_singleton(self):
        """Test that get_file_manager returns singleton"""
        manager1 = get_file_manager()
        manager2 = get_file_manager()
        
        assert manager1 is manager2
    
    @pytest.mark.asyncio
    async def test_file_lifecycle(self, file_manager, sample_file_data):
        """Test complete file lifecycle"""
        session_id = "test-session-id"
        
        with patch.object(file_manager.session_manager, 'validate_session') as mock_validate, \
             patch('app.services.file_manager.AsyncSessionLocal') as mock_db, \
             patch.object(file_manager.session_manager, 'get_session') as mock_get_session:
            
            mock_validate.return_value = True
            mock_get_session.return_value = MagicMock()
            
            mock_session = AsyncMock()
            mock_db.return_value.__aenter__.return_value = mock_session
            
            # Mock database operations
            mock_db_file = MagicMock()
            mock_db_file.id = "test-file-id"
            mock_db_file.name = sample_file_data.name
            mock_db_file.content = sample_file_data.content
            mock_db_file.language = sample_file_data.language.value
            mock_db_file.last_modified = datetime.utcnow()
            
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            mock_session.execute = AsyncMock()
            mock_session.delete = AsyncMock()
            
            # Create file
            file = await file_manager.create_file(session_id, sample_file_data)
            assert file is not None
            
            # Update file
            mock_result1 = AsyncMock()
            mock_result1.scalar_one_or_none.return_value = mock_db_file
            mock_result2 = AsyncMock()
            mock_result2.scalar_one.return_value = mock_db_file
            mock_session.execute.side_effect = [mock_result1, AsyncMock(), mock_result2]
            
            update_data = CodeFileUpdate(content="print('Updated')")
            updated_file = await file_manager.update_file(session_id, file.id, update_data)
            assert updated_file is not None
            
            # Delete file
            mock_result3 = AsyncMock()
            mock_result3.scalar_one_or_none.return_value = mock_db_file
            mock_session.execute.return_value = mock_result3
            
            success = await file_manager.delete_file(session_id, file.id)
            assert success is True


if __name__ == "__main__":
    pytest.main([__file__])