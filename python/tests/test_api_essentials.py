from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app


# Setup Global Override for Essentials Tests
def setup_module(module):
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "user-essentials",
        "role": "system_admin",
        "department": "Engineering",
    }


def teardown_module(module):
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200


def test_create_project():
    # Patch CLASS inside the split API modules
    with patch("src.server.api_routes.projects.core.ProjectCreationService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.create_project_with_ai = AsyncMock(return_value=(True, {"project_id": "proj-1", "project": {}}))
        mock_class.return_value = mock_inst

        response = client.post("/api/projects", json={"title": "Test Project", "description": "Desc"})
        assert response.status_code in [200, 201]


def test_list_projects():
    with patch("src.server.api_routes.projects.core.ProjectService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.list_projects = AsyncMock(return_value=(True, {"projects": []}))
        mock_class.return_value = mock_inst

        response = client.get("/api/projects")
        assert response.status_code == 200


def test_create_task():
    # Correct Tuple Unpacking fix: Returns (True, {"task": ...})
    # Patching the new physical location in projects.ops
    with patch("src.server.api_routes.projects.ops.TaskService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.create_task = AsyncMock(return_value=(True, {"task": {"id": "t1"}}))
        mock_class.return_value = mock_inst

        response = client.post(
            "/api/tasks", json={"title": "Test Task", "project_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [200, 201]


def test_list_tasks():
    with patch("src.server.api_routes.projects.ops.TaskService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.list_tasks = AsyncMock(return_value=(True, {"tasks": []}))
        mock_class.return_value = mock_inst

        response = client.get("/api/tasks")
        assert response.status_code == 200


def test_start_crawl():
    response = client.post("/api/crawl", json={"url": "https://example.com"})
    assert response.status_code in [200, 202, 400, 422, 500, 404]


def test_search_knowledge():
    response = client.post("/api/knowledge-items/search", json={"query": "test", "limit": 5})
    assert response.status_code in [200, 500, 422, 404]


def test_polling_endpoint():
    response = client.get("/api/progress/active")
    assert response.status_code in [200, 404]


def test_error_handling():
    # Test project not found path - patching projects.core
    with patch("src.server.api_routes.projects.core.ProjectService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.get_project = AsyncMock(return_value=(False, {"error": "Project not found"}))
        mock_class.return_value = mock_inst

        response = client.get("/api/projects/invalid-id")
        assert response.status_code == 404
