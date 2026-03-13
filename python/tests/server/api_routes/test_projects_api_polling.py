"""Unit tests for projects API polling endpoints with ETag support."""
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user

# 1. Correct import paths for physical dependency overrides
from src.server.main import app


# 2. Setup Global Overrides
def setup_module(module):
    # Ensure all routes have a system_admin context for polling tests
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "admin-polling",
        "role": "system_admin",
        "department": "Engineering"
    }

def teardown_module(module):
    app.dependency_overrides.pop(get_current_user, None)

# 3. Singleton Service Mocks
mock_task_service = AsyncMock()
mock_task_service_class = MagicMock(return_value=mock_task_service)
task_service_patch = patch('src.server.api_routes.projects_api.TaskService', mock_task_service_class)

# Apply patch for the entire module
task_service_patch.start()

client = TestClient(app)

class TestProjectsListPolling:
    def test_list_projects_http_with_etag(self):
        with patch('src.server.api_routes.projects_api.ProjectService') as mock_proj_class, \
             patch('src.server.api_routes.projects_api.SourceLinkingService') as mock_source_class:

            mock_proj_instance = MagicMock()
            mock_proj_instance.list_projects = AsyncMock(return_value=(True, {"projects": [{"id": "proj-1", "title": "Test Project", "department": "Engineering"}]}))
            mock_proj_class.return_value = mock_proj_instance

            mock_source_instance = MagicMock()
            mock_source_instance.format_projects_with_sources = AsyncMock(return_value=[{"id": "proj-1", "title": "Test Project", "department": "Engineering"}])
            mock_source_class.return_value = mock_source_instance

            response1 = client.get("/api/projects")
            assert response1.status_code == 200
            assert "ETag" in response1.headers
            etag = response1.headers["ETag"]

            response2 = client.get("/api/projects", headers={"If-None-Match": etag})
            assert response2.status_code == 304

class TestProjectTasksPolling:
    def test_list_project_tasks_http_polling(self):
        mock_task_service.reset_mock()
        mock_task_service.list_tasks = AsyncMock(return_value=(True, {"tasks": [{"id": "task-1", "title": "Test Task", "status": "todo"}]}))

        with patch('src.server.api_routes.projects_api.ProjectService') as mock_proj_class:
            mock_proj_instance = MagicMock()
            mock_proj_class.return_value = mock_proj_instance
            mock_proj_instance.get_project = AsyncMock(return_value=(True, {"project": {"id": "proj-1", "department": "Engineering"}}))

            response = client.get("/api/projects/proj-1/tasks")
            assert response.status_code == 200
            assert len(response.json()) == 1

class TestPollingEdgeCases:
    def test_project_not_found_no_etag(self):
        with patch('src.server.api_routes.projects_api.ProjectService') as mock_proj_class:
            mock_proj_instance = MagicMock()
            mock_proj_class.return_value = mock_proj_instance
            mock_proj_instance.get_project = AsyncMock(return_value=(False, {"error": "Project not found"}))

            response = client.get("/api/projects/non-existent")
            # Should be 404 or 403 based on current logic
            assert response.status_code in [404, 403]
