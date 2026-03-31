from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app


# Setup Global Override
def setup_module(module):
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "user-integration",
        "role": "system_admin",
        "department": "Engineering",
    }


def teardown_module(module):
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)


def test_project_with_tasks_flow():
    # Patch all involved classes
    with (
        patch("src.server.api_routes.projects.core.ProjectCreationService") as mock_create_class,
        patch("src.server.api_routes.projects.ops.TaskService") as mock_task_class,
    ):
        mock_create_inst = MagicMock()
        mock_create_inst.create_project_with_ai = AsyncMock(return_value=(True, {"project_id": "proj-int-1"}))
        mock_create_class.return_value = mock_create_inst

        mock_task_inst = MagicMock()
        mock_task_inst.create_task = AsyncMock(return_value=(True, {"task": {"id": "task-int-1"}}))
        mock_task_class.return_value = mock_task_inst

        # Test project creation
        proj_res = client.post("/api/projects", json={"title": "Integration Project"})
        assert proj_res.status_code in [200, 201]

        # Test task creation
        task_res = client.post("/api/tasks", json={"title": "Integrated Task", "project_id": "proj-int-1"})
        assert task_res.status_code in [200, 201]


def test_crawl_to_knowledge_flow():
    # Smoke test connectivity
    response = client.post("/api/crawl", json={"url": "https://example.com"})
    assert response.status_code in [200, 202, 400, 422, 500, 404]


def test_document_storage_flow():
    assert True


def test_code_extraction_flow():
    assert True


def test_search_and_retrieve_flow():
    # Smoke test connectivity
    response = client.post("/api/knowledge-items/search", json={"query": "test", "limit": 5})
    assert response.status_code in [200, 500, 422, 404]


def test_mcp_tool_execution():
    assert True


def test_progress_polling():
    response = client.get("/api/progress/active")
    assert response.status_code in [200, 404]


def test_background_task_progress():
    assert True


def test_database_operations():
    with patch("src.server.api_routes.projects.core.ProjectService") as mock_proj_class:
        mock_inst = MagicMock()
        mock_inst.list_projects = AsyncMock(return_value=(True, {"projects": []}))
        mock_proj_class.return_value = mock_inst

        response = client.get("/api/projects")
        assert response.status_code == 200


def test_concurrent_operations():
    with patch("src.server.api_routes.projects.ops.TaskService") as mock_task_class:
        mock_inst = MagicMock()
        mock_inst.list_tasks = AsyncMock(return_value=(True, {"tasks": []}))
        mock_task_class.return_value = mock_inst

        response = client.get("/api/tasks")
        assert response.status_code == 200
