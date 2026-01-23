from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient


@patch('src.server.api_routes.projects_api.TaskService', new_callable=MagicMock)
def test_list_tasks_admin_access(mock_task_service_class):
    """
    Test that admins can list all tasks (no assignee_id filter).
    """
    # Setup
    mock_task_service = mock_task_service_class.return_value
    mock_task_service.list_tasks = AsyncMock(return_value=(True, {"tasks": []}))

    # Mock authentication as Admin
    mock_admin_user = {"id": "admin-id", "role": "admin", "email": "admin@test.com"}

    from src.server.auth.dependencies import get_current_user
    from src.server.main import app

    # Override dependency
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    client = TestClient(app)

    # Execute
    response = client.get("/api/tasks")

    # Assert
    assert response.status_code == 200
    mock_task_service.list_tasks.assert_awaited_once()
    _, kwargs = mock_task_service.list_tasks.call_args

    # Admin should NOT have assignee_id filter (None)
    assert kwargs.get("assignee_id") is None

    # Cleanup
    app.dependency_overrides = {}

@patch('src.server.api_routes.projects_api.TaskService', new_callable=MagicMock)
def test_list_tasks_member_access(mock_task_service_class):
    """
    Test that regular members can only list their own tasks (assignee_id filter applied).
    """
    # Setup
    mock_task_service = mock_task_service_class.return_value
    mock_task_service.list_tasks = AsyncMock(return_value=(True, {"tasks": []}))

    # Mock authentication as Member
    mock_member_user = {"id": "user-123", "role": "member", "email": "user@test.com"}

    from src.server.auth.dependencies import get_current_user
    from src.server.main import app

    # Override dependency
    app.dependency_overrides[get_current_user] = lambda: mock_member_user

    client = TestClient(app)

    # Execute
    response = client.get("/api/tasks")

    # Assert
    assert response.status_code == 200
    mock_task_service.list_tasks.assert_awaited_once()
    _, kwargs = mock_task_service.list_tasks.call_args

    # Member MUST have assignee_id filter matching their user ID
    assert kwargs.get("assignee_id") == "user-123"
    # Ensure assignee_name is NOT passed (deprecated)
    assert kwargs.get("assignee_name") is None

    # Cleanup
    app.dependency_overrides = {}
