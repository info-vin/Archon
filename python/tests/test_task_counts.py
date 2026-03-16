from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user

# Correct import paths for physical dependency overrides
from src.server.main import app


# Setup Global Overrides for this test module
def setup_module(module):
    # Ensure all routes have a system_admin context for these tests
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "user-counts",
        "role": "system_admin",
        "department": "Engineering"
    }

def teardown_module(module):
    app.dependency_overrides.pop(get_current_user, None)

client = TestClient(app)

def test_batch_task_counts_endpoint():
    """Test the batch task counts endpoint with mocked service."""
    # We patch the CLASS itself where it is used in the API module
    with patch("src.server.api_routes.projects.ops.TaskService") as mock_service_class:
        # The constructor returns an instance
        mock_instance = MagicMock()
        mock_service_class.return_value = mock_instance

        # That instance has an async method that returns (success, data)
        mock_instance.get_all_project_task_counts = AsyncMock(return_value=(True, {"proj-1": {"todo": 5}}))

        response = client.get("/api/projects/task-counts")

        assert response.status_code == 200
        assert response.json() == {"proj-1": {"todo": 5}}

def test_batch_task_counts_etag_caching():
    """Test ETag caching for the batch task counts endpoint."""
    with patch("src.server.api_routes.projects.ops.TaskService") as mock_service_class:
        mock_instance = MagicMock()
        mock_service_class.return_value = mock_instance
        mock_instance.get_all_project_task_counts = AsyncMock(return_value=(True, {"proj-1": {"todo": 5}}))

        # First request to get the ETag
        response1 = client.get("/api/projects/task-counts")
        assert response1.status_code == 200
        etag = response1.headers.get("ETag")
        assert etag is not None

        # Second request with If-None-Match
        response2 = client.get("/api/projects/task-counts", headers={"If-None-Match": etag})
        assert response2.status_code == 304
        assert response2.content == b""
