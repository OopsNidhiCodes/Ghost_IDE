"""
Integration tests with real database operations
"""

import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def get_test_db():
    """Override database dependency for testing"""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest.fixture
async def setup_test_db():
    """Setup test database and override dependency"""
    # Override the dependency
    app.dependency_overrides[get_db] = get_test_db
    
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Cleanup
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Remove override
    if get_db in app.dependency_overrides:
        del app.dependency_overrides[get_db]


class TestSessionIntegration:
    """Integration tests for session management"""
    
    @pytest.mark.asyncio
    async def test_create_and_get_session(self, setup_test_db):
        """Test creating and retrieving a session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create session
            session_data = {
                "current_language": "python",
                "preferences": {
                    "theme": "ghost-dark",
                    "font_size": 16,
                    "auto_save": True,
                    "auto_save_interval": 45
                }
            }
            
            create_response = await client.post("/api/v1/sessions/", json=session_data)
            assert create_response.status_code == 200
            
            create_data = create_response.json()
            assert create_data["success"] is True
            assert "👻" in create_data["message"]
            
            session = create_data["session"]
            session_id = session["id"]
            assert session["current_language"] == "python"
            assert session["preferences"]["font_size"] == 16
            
            # Get session
            get_response = await client.get(f"/api/v1/sessions/{session_id}")
            assert get_response.status_code == 200
            
            get_data = get_response.json()
            assert get_data["success"] is True
            assert get_data["session"]["id"] == session_id
    
    @pytest.mark.asyncio
    async def test_session_with_files(self, setup_test_db):
        """Test session with file operations"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create session
            create_response = await client.post("/api/v1/sessions/", json={})
            session_id = create_response.json()["session"]["id"]
            
            # Create file
            file_data = {
                "name": "main.py",
                "content": "print('Hello Ghost!')",
                "language": "python"
            }
            
            file_response = await client.post(
                f"/api/v1/sessions/{session_id}/files",
                json=file_data
            )
            assert file_response.status_code == 200
            
            file_result = file_response.json()
            assert file_result["name"] == "main.py"
            assert file_result["content"] == "print('Hello Ghost!')"
            
            # Get all files
            files_response = await client.get(f"/api/v1/sessions/{session_id}/files")
            assert files_response.status_code == 200
            
            files = files_response.json()
            assert len(files) == 1
            assert files[0]["name"] == "main.py"