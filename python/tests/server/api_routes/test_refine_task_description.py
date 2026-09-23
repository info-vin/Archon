import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from src.server.main import app
from src.server.models.auth_models import UserProfileDTO
from src.server.auth.dependencies import get_current_user

@pytest.fixture
def mock_current_user():
    return UserProfileDTO(
        id="user-123",
        email="test@example.com",
        name="Test User",
        role="member",
        department="Engineering",
    )

def test_refine_task_description_endpoint(mock_current_user):
    with patch("src.server.api_routes.projects.ops.TaskService.refine_task_description", new_callable=AsyncMock) as mock_refine:
        mock_refine.return_value = "Refined description output"

        app.dependency_overrides[get_current_user] = lambda: mock_current_user
        client = TestClient(app)

        response = client.post(
            "/api/tasks/refine-description",
            json={"title": "Draft Title", "description": "Draft Description"}
        )

        app.dependency_overrides.clear()

        assert response.status_code == 200
        assert response.json() == {"refined_description": "Refined description output"}
