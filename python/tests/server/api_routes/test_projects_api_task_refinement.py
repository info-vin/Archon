from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.server.main import app
from src.server.models.auth_models import UserProfileDTO

client = TestClient(app)


def test_refine_task_description_success():
    """Test successful task description refinement via POST /api/tasks/refine-description."""
    mock_user = UserProfileDTO(
        id="user-123",
        email="test@example.com",
        role="member",
        department="Engineering",
    )

    app.dependency_overrides = {}
    from src.server.auth.dependencies import get_current_user

    app.dependency_overrides[get_current_user] = lambda: mock_user

    try:
        with patch("src.server.api_routes.projects.ops.TaskService") as mock_service_cls:
            mock_service_inst = mock_service_cls.return_value
            mock_service_inst.refine_task_description = AsyncMock(return_value="Refined description by AI.")

            payload = {
                "title": "Initial Task Title",
                "description": "Initial rough description",
            }

            response = client.post("/api/tasks/refine-description", json=payload)

            assert response.status_code == 200
            json_resp = response.json()
            assert json_resp == {"refined_description": "Refined description by AI."}
            mock_service_inst.refine_task_description.assert_awaited_once_with(
                "Initial Task Title", "Initial rough description"
            )
    finally:
        app.dependency_overrides.clear()
