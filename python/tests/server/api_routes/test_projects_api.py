from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock

@patch('src.server.api_routes.projects_api.TaskService')
def test_update_task_succeeds(mock_task_service_class, client: TestClient):
    """
    Tests that updating a task via the PUT /api/tasks/{task_id} endpoint
    succeeds and calls the underlying TaskService correctly.
    This test acts as a regression test for the 'cannot edit task' bug.
    """
    # Arrange
    # Configure the mock instance that will be created inside the endpoint
    mock_instance = mock_task_service_class.return_value
    
    # The service method is expected to return a tuple: (success, result_dict)
    mock_service_result = {
        "task": {
            "id": "task-123",
            "title": "Updated Title",
            "description": "Updated description"
        }
    }
    mock_instance.update_task = AsyncMock(return_value=(True, mock_service_result))

    update_payload = {
        "title": "Updated Title",
        "description": "Updated description"
    }

    # Act
    response = client.put(
        "/api/tasks/task-123",
        json=update_payload
    )

    # Assert
    # 1. Assert the HTTP response is correct
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["message"] == "Task updated successfully"
    assert response_data["task"]["title"] == "Updated Title"

    # 2. Assert that the service was instantiated and the method was called correctly
    mock_task_service_class.assert_called_once()
    mock_instance.update_task.assert_called_once_with("task-123", update_payload)
