from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO


@pytest.fixture
def dummy_user():
    return UserProfileDTO(id="user-123", role="admin", email="test@archon.com")


@pytest.fixture
def client(dummy_user):
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_get_project_features_contract(client):
    mock_features_payload = {
        "features": [
            {
                "id": "feat-1",
                "label": "Authentication",
                "type": "security",
                "color": "blue",
                "status": "completed",
                "custom_metadata": {"components": ["oauth", "jwt"]},
            },
            {
                "id": "feat-2",
                "label": "API Gateway",
                "name": "api_gateway",
                "version": "2.0",
                "endpoints_done": 12,
            },
        ]
    }

    with patch("src.server.api_routes.projects.core.ProjectService") as mock_service_cls:
        instance = mock_service_cls.return_value
        instance.get_project_features = AsyncMock(return_value=(True, mock_features_payload))

        response = client.get("/api/projects/proj-123/features")

        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        assert "count" in data
        assert data["count"] == 2
        assert len(data["features"]) == 2

        feat1 = data["features"][0]
        assert feat1["id"] == "feat-1"
        assert feat1["label"] == "Authentication"
        assert feat1["type"] == "security"
        assert feat1["color"] == "blue"
        assert feat1["status"] == "completed"
        assert feat1["custom_metadata"] == {"components": ["oauth", "jwt"]}

        feat2 = data["features"][1]
        assert feat2["id"] == "feat-2"
        assert feat2["label"] == "API Gateway"
        assert feat2["name"] == "api_gateway"
        assert feat2["version"] == "2.0"
        assert feat2["endpoints_done"] == 12


def test_get_project_features_not_found(client):
    with patch("src.server.api_routes.projects.core.ProjectService") as mock_service_cls:
        instance = mock_service_cls.return_value
        instance.get_project_features = AsyncMock(return_value=(False, "Project features not found"))

        response = client.get("/api/projects/non-existent/features")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
