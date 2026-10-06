from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.server.api_routes.admin_api import router
from src.server.auth.dependencies import get_current_user
from src.server.models.auth_models import UserProfileDTO

app = FastAPI()
app.include_router(router)

def mock_manager_user():
    return UserProfileDTO(id="mgr-123", role="manager", email="mgr@archon.com", department="Engineering")

def mock_admin_user():
    return UserProfileDTO(id="admin-123", role="admin", email="admin@archon.com", department="Executive")

def test_get_admin_logs_success():
    app.dependency_overrides[get_current_user] = mock_manager_user
    mock_logs = [
        {
            "id": "log-1",
            "source": "scheduler",
            "level": "INFO",
            "message": "Job executed successfully",
            "details": {"job_id": "test_job"},
            "created_at": "2025-01-01T00:00:00Z",
            "type": "AI_CORRECTION",
        }
    ]
    with patch("src.server.api_routes.admin_api.admin_service.get_admin_logs", new_callable=AsyncMock) as mock_get_logs:
        mock_get_logs.return_value = mock_logs
        client = TestClient(app)
        response = client.get("/api/admin/logs?type=AI_CORRECTION&time_range=7d")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "log-1"
        assert data[0]["source"] == "scheduler"
        assert data[0]["type"] == "AI_CORRECTION"
        mock_get_logs.assert_awaited_once_with(type="AI_CORRECTION", time_range="7d")
    app.dependency_overrides.clear()


def test_trigger_scheduler_job_success():
    app.dependency_overrides[get_current_user] = mock_manager_user
    client = TestClient(app)
    response = client.post("/api/admin/scheduler/job/system_probe/run")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "triggered", "job_id": "system_probe"}
    app.dependency_overrides.clear()


def test_trigger_scheduler_job_unknown_job():
    app.dependency_overrides[get_current_user] = mock_manager_user
    client = TestClient(app)
    response = client.post("/api/admin/scheduler/job/nonexistent_job/run")
    assert response.status_code == 400
    data = response.json()
    assert "Unknown job_id" in data["detail"]
    app.dependency_overrides.clear()


def test_delete_crawler_target_success():
    app.dependency_overrides[get_current_user] = mock_manager_user
    with patch("src.server.api_routes.admin_api.admin_service.delete_crawler_target", new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = None
        client = TestClient(app)
        response = client.delete("/api/admin/crawler-targets/target-123")
        assert response.status_code == 200
        data = response.json()
        assert data == {"success": True}
        mock_delete.assert_awaited_once_with("target-123")
    app.dependency_overrides.clear()


def test_get_document_versions_success():
    app.dependency_overrides[get_current_user] = mock_admin_user
    mock_versions = [
        {
            "id": "ver-1",
            "document_id": "doc-100",
            "created_by": "admin-123",
            "change_type": "update",
            "field_name": "title",
            "old_value": "Old Title",
            "new_value": "New Title",
            "change_summary": "Updated document title",
            "version_number": 2,
            "created_at": "2025-01-01T12:00:00Z",
        }
    ]
    with patch("src.server.api_routes.admin_api.admin_service.get_document_versions", new_callable=AsyncMock) as mock_get_versions:
        mock_get_versions.return_value = mock_versions
        client = TestClient(app)
        response = client.get("/api/admin/document-versions?limit=50")
        assert response.status_code == 200
        data = response.json()
        assert "versions" in data
        assert len(data["versions"]) == 1
        assert data["versions"][0]["id"] == "ver-1"
        assert data["versions"][0]["document_id"] == "doc-100"
        assert data["versions"][0]["version_number"] == 2
        mock_get_versions.assert_awaited_once_with(limit=50)
    app.dependency_overrides.clear()


def test_get_document_versions_failure():
    app.dependency_overrides[get_current_user] = mock_admin_user
    with patch("src.server.api_routes.admin_api.admin_service.get_document_versions", new_callable=AsyncMock) as mock_get_versions:
        mock_get_versions.side_effect = Exception("Database connection error")
        client = TestClient(app)
        response = client.get("/api/admin/document-versions")
        assert response.status_code == 200
        data = response.json()
        assert data == {"versions": []}
    app.dependency_overrides.clear()
