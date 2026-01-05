from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

# 1. Create mocks BEFORE app import
mock_task_service = AsyncMock()
mock_task_service_class = MagicMock(return_value=mock_task_service)

# Patch the TaskService class used in the API module
task_service_patch = patch('src.server.api_routes.projects_api.TaskService', mock_task_service_class)

def setup_module(module):
    task_service_patch.start()

def teardown_module(module):
    task_service_patch.stop()

from src.server.main import app  # noqa: E402

# 5. Create a single, shared TestClient
client = TestClient(app)


def test_report_task_status_from_agent_success():
    """Test successful reporting of task status from an agent."""
    # Reset and configure mock for this test
    mock_task_service.reset_mock()
    task_id = "test-task-uuid"
    agent_id = "ai-dev-agent"
    status = "completed"

    mock_task_service.update_task_status_from_agent = AsyncMock(return_value=(
        True,
        {"task": {"id": task_id, "status": status, "assignee": agent_id}},
    ))

    response = client.post(
        f"/api/tasks/{task_id}/agent-status", json={"status": status, "agent_id": agent_id}
    )

    assert response.status_code == 200
    assert response.json()["task"]["status"] == status
    mock_task_service.update_task_status_from_agent.assert_awaited_once_with(
        task_id=task_id, new_status=status, agent_id=agent_id
    )


def test_report_task_status_from_agent_failure():
    """Test failure when reporting task status from an agent."""
    # Reset and configure mock for this test
    mock_task_service.reset_mock()
    task_id = "test-task-uuid"
    agent_id = "ai-dev-agent"
    status = "invalid_status"

    mock_task_service.update_task_status_from_agent = AsyncMock(return_value=(
        False,
        {"error": "Invalid status provided"},
    ))

    response = client.post(
        f"/api/tasks/{task_id}/agent-status", json={"status": status, "agent_id": agent_id}
    )

    assert response.status_code == 400
    assert "Invalid status provided" in response.json()["detail"]
    mock_task_service.update_task_status_from_agent.assert_awaited_once_with(
        task_id=task_id, new_status=status, agent_id=agent_id
    )


def test_report_task_output_from_agent_success():
    """Test successful reporting of task output from an agent."""
    # Reset and configure mock for this test
    mock_task_service.reset_mock()
    task_id = "test-task-uuid"
    agent_id = "ai-dev-agent"
    output_data = {"summary": "Generated code for auth module"}

    mock_task_service.save_agent_output = AsyncMock(return_value=(
        True,
        {"task": {"id": task_id, "assignee": agent_id, "attachments": [output_data]}},
    ))

    response = client.post(
        f"/api/tasks/{task_id}/agent-output", json={"output": output_data, "agent_id": agent_id}
    )

    assert response.status_code == 200
    assert response.json()["task"]["attachments"][0] == output_data
    mock_task_service.save_agent_output.assert_awaited_once_with(
        task_id=task_id, output=output_data, agent_id=agent_id
    )


def test_report_task_output_from_agent_failure():
    """Test failure when reporting task output from an agent."""
    # Reset and configure mock for this test
    mock_task_service.reset_mock()
    task_id = "test-task-uuid"
    agent_id = "ai-dev-agent"
    output_data = {"error_reason": "Code generation failed"}

    mock_task_service.save_agent_output = AsyncMock(return_value=(
        False,
        {"error": "Failed to store output"},
    ))

    response = client.post(
        f"/api/tasks/{task_id}/agent-output", json={"output": output_data, "agent_id": agent_id}
    )

    assert response.status_code == 400
    assert "Failed to store output" in response.json()["detail"]
    mock_task_service.save_agent_output.assert_awaited_once_with(
        task_id=task_id, output=output_data, agent_id=agent_id
    )
