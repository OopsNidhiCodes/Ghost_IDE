"""
Unit tests for API endpoints
"""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.models.schemas import UserSessionCreate, CodeFileCreate, LanguageType


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


# Override the dependency
app.dependency_overrides[get_db] = get_test_db


@pytest.fixture
async def setup_database():
    """Setup test database"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "👻" in data["message"]
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"
        assert "👻" in data["message"]


class TestSessionEndpoints:
    """Test session management endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_session(self, setup_database):
        """Test creating a new session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            session_data = {
                "current_language": "python",
                "preferences": {
                    "theme": "ghost-dark",
                    "font_size": 16,
                    "auto_save": True,
                    "auto_save_interval": 45
                }
            }
            
            response = await client.post("/api/v1/sessions/", json=session_data)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "👻" in data["message"]
            assert data["session"] is not None
            assert data["session"]["current_language"] == "python"
            assert data["session"]["preferences"]["font_size"] == 16
    
    @pytest.mark.asyncio
    async def test_create_session_with_defaults(self, setup_database):
        """Test creating session with default values"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            session_data = {}
            
            response = await client.post("/api/v1/sessions/", json=session_data)
            assert response.status_code == 200
            
            data = response.json()
            session = data["session"]
            assert session["current_language"] == "python"
            assert session["preferences"]["theme"] == "ghost-dark"
            assert session["preferences"]["font_size"] == 14
            assert session["files"] == []
            assert session["chat_history"] == []
    
    @pytest.mark.asyncio
    async def test_get_session(self, setup_database):
        """Test retrieving a session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create session first
            create_response = await client.post("/api/v1/sessions/", json={})
            session_id = create_response.json()["session"]["id"]
            
            # Get session
            response = await client.get(f"/api/v1/sessions/{session_id}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["session"]["id"] == session_id
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, setup_database):
        """Test retrieving a non-existent session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/v1/sessions/nonexistent-id")
            assert response.status_code == 404
            assert "👻" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_update_session(self, setup_database):
        """Test updating a session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create session first
            create_response = await client.post("/api/v1/sessions/", json={})
            session_id = create_response.json()["session"]["id"]
            
            # Update session
            update_data = {
                "current_language": "javascript",
                "preferences": {
                    "theme": "ghost-light",
                    "font_size": 18
                }
            }
            
            response = await client.put(f"/api/v1/sessions/{session_id}", json=update_data)
            assert response.status_code == 200
            
            data = response.json()
            session = data["session"]
            assert session["current_language"] == "javascript"
            assert session["preferences"]["theme"] == "ghost-light"
            assert session["preferences"]["font_size"] == 18
    
    @pytest.mark.asyncio
    async def test_delete_session(self, setup_database):
        """Test deleting a session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create session first
            create_response = await client.post("/api/v1/sessions/", json={})
            session_id = create_response.json()["session"]["id"]
            
            # Delete session
            response = await client.delete(f"/api/v1/sessions/{session_id}")
            assert response.status_code == 200
            assert "👻" in response.json()["message"]
            
            # Verify session is deleted
            get_response = await client.get(f"/api/v1/sessions/{session_id}")
            assert get_response.status_code == 404


class TestFileEndpoints:
    """Test file management endpoints"""
    
    @pytest.mark.asyncio
    async def test_create_file(self, setup_database):
        """Test creating a file in a session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create session first
            create_response = await client.post("/api/v1/sessions/", json={})
            session_id = create_response.json()["session"]["id"]
            
            # Create file
            file_data = {
                "name": "main.py",
                "content": "print('Hello Ghost!')",
                "language": "python"
            }
            
            response = await client.post(
                f"/api/v1/sessions/{session_id}/files",
                json=file_data
            )
            assert response.status_code == 200
            
            data = response.json()
            assert data["name"] == "main.py"
            assert data["content"] == "print('Hello Ghost!')"
            assert data["language"] == "python"
            assert "id" in data
            assert "last_modified" in data
    
    @pytest.mark.asyncio
    async def test_create_file_invalid_session(self, setup_database):
        """Test creating file in non-existent session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            file_data = {
                "name": "test.py",
                "content": "print('test')",
                "language": "python"
            }
            
            response = await client.post(
                "/api/v1/sessions/nonexistent/files",
                json=file_data
            )
            assert response.status_code == 404
            assert "👻" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_get_session_files(self, setup_database):
        """Test getting all files in a session"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create session
            create_response = await client.post("/api/v1/sessions/", json={})
            session_id = create_response.json()["session"]["id"]
            
            # Create multiple files
            files = [
                {"name": "main.py", "content": "print('Hello')", "language": "python"},
                {"name": "script.js", "content": "console.log('Hi')", "language": "javascript"}
            ]
            
            for file_data in files:
                await client.post(f"/api/v1/sessions/{session_id}/files", json=file_data)
            
            # Get all files
            response = await client.get(f"/api/v1/sessions/{session_id}/files")
            assert response.status_code == 200
            
            data = response.json()
            assert len(data) == 2
            assert any(f["name"] == "main.py" for f in data)
            assert any(f["name"] == "script.js" for f in data)
    
    @pytest.mark.asyncio
    async def test_get_files_empty_session(self, setup_database):
        """Test getting files from session with no files"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Create session
            create_response = await client.post("/api/v1/sessions/", json={})
            session_id = create_response.json()["session"]["id"]
            
            # Get files
            response = await client.get(f"/api/v1/sessions/{session_id}/files")
            assert response.status_code == 200
            
            data = response.json()
            assert data == []