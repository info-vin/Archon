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
