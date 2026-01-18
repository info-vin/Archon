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

@patch('src.server.api_routes.projects_api.ProfileService', new_callable=MagicMock)
@patch('src.server.api_routes.projects_api.TaskService', new_callable=MagicMock)
def test_list_tasks_member_access(mock_task_service_class, mock_profile_service_class):
    """
    Test that regular members can only list their own tasks (assignee_name filter applied).
    """
    # Setup
    mock_task_service = mock_task_service_class.return_value
    mock_task_service.list_tasks = AsyncMock(return_value=(True, {"tasks": []}))

    # Mock Profile Service to resolve UUID to Name
    mock_profile_service = mock_profile_service_class.return_value
    mock_profile_service.get_profile.return_value = (True, {"name": "Alice Johnson"})

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

    # Member MUST have assignee_name filter resolved from their profile
    assert kwargs.get("assignee_name") == "Alice Johnson"

    # Cleanup
    app.dependency_overrides = {}
