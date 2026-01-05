from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


# To test the API routes in isolation, we patch the services they depend on.
# These patches target the namespaces where the services are imported and used.
@patch('src.server.api_routes.projects_api.TaskService', new_callable=MagicMock)
@patch('src.server.api_routes.projects_api.RBACService', new_callable=MagicMock)
@patch('src.server.api_routes.projects_api.ProfileService', new_callable=MagicMock)
def test_create_task_with_ai_assignee_success(mock_profile_class, mock_rbac_class, mock_task_service_class):
    """
    Unit test for the POST /tasks endpoint.
    Verifies that with correct permissions, the endpoint correctly calls the task_service.
    """
    # --- Setup Mocks ---
    # 1. RBAC service mock: Assume the permission check passes.
    mock_rbac_instance = mock_rbac_class.return_value
    mock_rbac_instance.has_permission_to_assign.return_value = True

    # 2. Profile service mock: Assume we can get the assignee's role.
    mock_profile_instance = mock_profile_class.return_value
    mock_profile_instance.get_user_role.return_value = (True, "ai-researcher-1")

    # 3. Task service mock: Configure create_task to be an AsyncMock.
    mock_task_service_instance = mock_task_service_class.return_value
    mock_task_service_instance.create_task = AsyncMock(return_value=(True, {"task": {"id": "new-task-id"}}))

    # --- Test Execution ---
    from src.server.main import app
    client = TestClient(app)

    task_payload = {
        "project_id": "proj-123",
        "title": "Test AI Task",
        "assignee": "ai-researcher-1"
    }
    headers = {"X-User-Role": "Admin"}

    response = client.post("/api/tasks", json=task_payload, headers=headers)

    # --- Assertions ---
    assert response.status_code == 200
    assert response.json()["task"]["id"] == "new-task-id"

    # Verify that the API route logic correctly called the task service
    mock_task_service_instance.create_task.assert_awaited_once()
    _, called_kwargs = mock_task_service_instance.create_task.call_args
    assert called_kwargs["project_id"] == "proj-123"
    assert called_kwargs["title"] == "Test AI Task"
    assert called_kwargs["assignee"] == "ai-researcher-1"


@patch('src.server.api_routes.projects_api.TaskService', new_callable=MagicMock)
@patch('src.server.api_routes.projects_api.RBACService', new_callable=MagicMock)
@patch('src.server.api_routes.projects_api.ProfileService', new_callable=MagicMock)
def test_create_task_with_ai_assignee_permission_denied(mock_profile_class, mock_rbac_class, mock_task_service_class):
    """
    Unit test for the POST /tasks endpoint.
    Verifies that if the RBAC check fails, the endpoint returns a 403 Forbidden.
    """
    # --- Setup Mocks ---
    # 1. RBAC service mock: This time, the permission check fails.
    mock_rbac_instance = mock_rbac_class.return_value
    mock_rbac_instance.has_permission_to_assign.return_value = False

    # 2. Profile service mock
    mock_profile_instance = mock_profile_class.return_value
    mock_profile_instance.get_user_role.return_value = (True, "ai-researcher-1")

    mock_task_service_instance = mock_task_service_class.return_value

    # --- Test Execution ---
    from src.server.main import app
    client = TestClient(app)

    task_payload = {
        "project_id": "proj-123",
        "title": "Test AI Task",
        "assignee": "ai-researcher-1"
    }
    headers = {"X-User-Role": "User"}

    response = client.post("/api/tasks", json=task_payload, headers=headers)

    # --- Assertions ---
    assert response.status_code == 403
    assert "you cannot assign tasks" in response.json()["detail"]

    # Verify the task service was NOT called because the permission check failed first.
    mock_task_service_instance.create_task.assert_not_called()


@patch('src.server.api_routes.projects_api.TaskService', new_callable=MagicMock)
@patch('src.server.api_routes.projects_api.RBACService', new_callable=MagicMock)
@patch('src.server.api_routes.projects_api.ProfileService', new_callable=MagicMock)
def test_create_task_with_knowledge_sources(mock_profile_class, mock_rbac_class, mock_task_service_class):
    """
    Unit test for the POST /tasks endpoint with knowledge_source_ids.
    Verifies that knowledge_source_ids are passed to the task service.
    """
    # --- Setup Mocks ---
    mock_rbac_instance = mock_rbac_class.return_value
    mock_rbac_instance.has_permission_to_assign.return_value = True

    mock_task_service_instance = mock_task_service_class.return_value
    mock_task_service_instance.create_task = AsyncMock(return_value=(True, {"task": {"id": "new-task-id"}}))

    # --- Test Execution ---
    from src.server.main import app
    client = TestClient(app)

    task_payload = {
        "project_id": "proj-123",
        "title": "Task with Knowledge",
        "knowledge_source_ids": ["source-1", "source-2"]
    }

    response = client.post("/api/tasks", json=task_payload)

    # --- Assertions ---
    assert response.status_code == 200
    assert response.json()["task"]["id"] == "new-task-id"

    # Verify that the API route logic correctly called the task service with knowledge_source_ids
    mock_task_service_instance.create_task.assert_awaited_once()
    _, called_kwargs = mock_task_service_instance.create_task.call_args
    assert called_kwargs["project_id"] == "proj-123"
    assert called_kwargs["title"] == "Task with Knowledge"
    assert called_kwargs["knowledge_source_ids"] == ["source-1", "source-2"]
