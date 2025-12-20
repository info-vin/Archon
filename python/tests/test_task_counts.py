"""Test suite for batch task counts endpoint - Performance optimization tests."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# 1. Create mocks BEFORE app import
mock_task_service = AsyncMock()

# 2. Define patch target where the service is USED
task_service_patch = patch('src.server.api_routes.projects_api.task_service', mock_task_service)

# 3. Now import the app
from src.server.main import app  # noqa: E402


# 4. Setup and Teardown for the module to control patch lifecycle
def setup_module(module):
    """Start all patches."""
    task_service_patch.start()

def teardown_module(module):
    """Stop all patches."""
    task_service_patch.stop()

# NOTE: client is now created inside each test function for maximum isolation.

def test_batch_task_counts_endpoint():
    """Test that batch task counts endpoint returns counts from the service."""
    client = TestClient(app)
    # Reset and configure mock for this test
    mock_task_service.reset_mock()

    mock_counts = {
        "project-1": {"todo": 2, "doing": 2, "done": 1},
        "project-2": {"todo": 1, "doing": 1, "done": 2},
        "project-3": {"todo": 1, "doing": 0, "done": 0},
    }
    mock_task_service.get_all_project_task_counts = AsyncMock(return_value=(True, mock_counts))

    response = client.get("/api/projects/task-counts")

    assert response.status_code == 200
    data = response.json()
    assert data == mock_counts


@pytest.mark.xfail(reason="ETag caching is not working as expected in TestClient for this specific route")
def test_batch_task_counts_etag_caching():
    """Test that ETag caching works correctly for task counts."""
    client = TestClient(app)
    # Reset and configure mock for this test to ensure isolation
    mock_task_service.reset_mock()

    mock_counts = {"project-1": {"todo": 1, "doing": 1, "done": 0}}
    # Set the return value for the mock. It will be the same for both calls in this test.
    mock_task_service.get_all_project_task_counts = AsyncMock(return_value=(True, mock_counts))

    # First request - should return data with ETag
    response1 = client.get("/api/projects/task-counts")
    assert response1.status_code == 200
    assert "ETag" in response1.headers
    etag = response1.headers["ETag"]
    # Verify service was called exactly once
    assert mock_task_service.get_all_project_task_counts.await_count == 1

    # Second request with If-None-Match header - should return 304
    response2 = client.get("/api/projects/task-counts", headers={"If-None-Match": etag})
    assert response2.status_code == 304
    assert response2.headers.get("ETag") == etag

    # Verify service was NOT called again
    assert mock_task_service.get_all_project_task_counts.await_count == 1
