from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from server.auth.dependencies import get_current_user
from server.main import app
from server.models.auth_models import UserProfileDTO

client = TestClient(app)


@pytest.fixture
def mock_team_user():
    user = {"id": "user1", "role": "admin", "email": "admin@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(**user)
    yield user
    app.dependency_overrides = {}


def test_get_current_version():
    response = client.get("/api/version/current")
    assert response.status_code == 200
    data = response.json()
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_clear_version_cache():
    with patch("server.api_routes.version_api.version_service.clear_cache") as mock_clear:
        response = client.post("/api/version/clear-cache")
        assert response.status_code == 200
        data = response.json()
        assert data == {"message": "Version cache cleared successfully", "success": True}
        assert mock_clear.called


@pytest.mark.asyncio
async def test_get_document_versions(mock_team_user):
    mock_docs = [
        {
            "id": "v1",
            "project_id": "p1",
            "task_id": "t1",
            "field_name": "doc",
            "version_number": 1,
            "content": {"key": "val"},
            "change_summary": "init",
            "change_type": "create",
            "document_id": "d1",
            "created_by": "u1",
            "created_at": "2025-01-01T00:00:00Z",
            "status": "active",
        }
    ]
    with patch("server.api_routes.version_api.version_service.get_document_versions", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_docs
        response = client.get("/api/version/documents")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "v1"
        assert data[0]["version_number"] == 1


@pytest.mark.asyncio
async def test_check_for_updates():
    mock_check_data = {
        "current": "1.0.0",
        "latest": "1.1.0",
        "update_available": True,
        "release_url": "https://github.com/org/repo/releases/tag/v1.1.0",
        "release_notes": "Notes",
        "published_at": None,
        "check_error": None,
        "assets": [],
        "author": "user",
    }
    with patch("server.api_routes.version_api.version_service.check_for_updates", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = mock_check_data
        response = client.get("/api/version/check")
        assert response.status_code == 200
        data = response.json()
        assert data["current"] == "1.0.0"
        assert data["latest"] == "1.1.0"
        assert data["update_available"] is True
