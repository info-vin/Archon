"""Unit tests for projects API polling endpoints with ETag support."""
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

# 1. Create a mock for the ONE service that is a module-level singleton
mock_task_service = AsyncMock()

# 2. Define the patch target for that singleton where it is USED
task_service_patch = patch('src.server.api_routes.projects_api.task_service', mock_task_service)

# 3. Now import the app
from src.server.main import app  # noqa: E402


# 4. Setup and Teardown for the module to control the patch lifecycle
def setup_module(module):
    """Start all patches."""
    task_service_patch.start()

def teardown_module(module):
    """Stop all patches."""
    task_service_patch.stop()

# 5. Create a single, shared TestClient
client = TestClient(app)


class TestProjectsListPolling:
    """Tests for projects list endpoint with polling support."""

    def test_list_projects_http_with_etag(self):
        """
        Test projects endpoint via HTTP with ETag support.
        This test now patches the services instantiated inside the route.
        """
        # For services instantiated inside the route, we patch them directly here
        with patch('src.server.api_routes.projects_api.ProjectService') as mock_proj_class, \
             patch('src.server.api_routes.projects_api.SourceLinkingService') as mock_source_class:

            # Configure the mock for ProjectService
            mock_proj_instance = MagicMock()
            # list_projects is async, so its mock must be an AsyncMock
            mock_proj_instance.list_projects = AsyncMock(return_value=(True, {"projects": [{"id": "proj-1", "name": "Test Project"}]}))
            mock_proj_class.return_value = mock_proj_instance

            # Configure the mock for SourceLinkingService (which is synchronous)
            mock_source_instance = MagicMock()
            mock_source_instance.format_projects_with_sources.return_value = [{"id": "proj-1", "name": "Test Project"}]
            mock_source_class.return_value = mock_source_instance

            # First request
            response1 = client.get("/api/projects")
            assert response1.status_code == 200
            assert "ETag" in response1.headers
            etag = response1.headers["ETag"]

            # Second request with If-None-Match
            response2 = client.get("/api/projects", headers={"If-None-Match": etag})
            assert response2.status_code == 304
            assert response2.content == b""


class TestProjectTasksPolling:
    """Tests for project tasks endpoint with polling support."""

    def test_list_project_tasks_http_polling(self):
        """Test project tasks endpoint polling via HTTP."""
        # Reset the module-level mock for this test
        mock_task_service.reset_mock()

        # This route uses the singleton task_service, so we configure it directly.
        mock_task_service.list_tasks = AsyncMock(return_value=(True, {"tasks": [
            {"id": "task-1", "title": "Test Task", "status": "todo"},
        ]}))

        etag = None
        for i in range(2):
            # This route instantiates ProjectService, so we must patch it here
            with patch('src.server.api_routes.projects_api.ProjectService') as mock_proj_class:
                mock_proj_instance = MagicMock()
                mock_proj_class.return_value = mock_proj_instance
                mock_proj_instance.get_project.return_value = (True, {"id": "proj-1"})

                headers = {"If-None-Match": etag} if etag else {}
                response = client.get("/api/projects/proj-1/tasks", headers=headers)

                if i == 0:
                    assert response.status_code == 200
                    assert len(response.json()) == 1
                    etag = response.headers["ETag"]
                else:
                    assert response.status_code == 304
                    assert response.content == b""

        mock_task_service.list_tasks.assert_awaited()


class TestPollingEdgeCases:
    """Test edge cases in polling implementation."""

    def test_project_not_found_no_etag(self):
        """
        Test that 404 responses don't include ETags for the get_project route.
        """
        # This test targets the get_project route, which instantiates ProjectService
        with patch('src.server.api_routes.projects_api.ProjectService') as mock_proj_class:
            mock_proj_instance = MagicMock()
            mock_proj_class.return_value = mock_proj_instance
            mock_proj_instance.get_project.return_value = (False, {"error": "Project not found"})

            response = client.get("/api/projects/non-existent")

            assert response.status_code == 404
            assert "ETag" not in response.headers
