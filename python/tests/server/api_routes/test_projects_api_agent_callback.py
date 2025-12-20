import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.main import app
from src.server.services.projects.task_service import TaskService


@pytest.fixture(name="client")
def client_fixture():
    """Test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(name="mock_task_service")
def mock_task_service_fixture():
    """Mock TaskService dependency."""
    with patch("src.server.api_routes.projects_api.TaskService") as MockClass:
        mock_instance = MockClass.return_value
        yield mock_instance


@pytest.mark.asyncio
async def test_report_task_status_from_agent_success(
    client: TestClient, mock_task_service: AsyncMock
):
    """Test successful reporting of task status from an agent."""
    task_id = "test-task-uuid"
    agent_id = "ai-dev-agent"
    status = "completed"

    mock_task_service.update_task_status_from_agent.return_value = (
        True,
        {"task": {"id": task_id, "status": status, "assignee": agent_id}},
    )

    response = client.post(
        f"/api/tasks/{task_id}/agent-status", json={"status": status, "agent_id": agent_id}
    )

    assert response.status_code == 200
    assert response.json()["task"]["status"] == status
    mock_task_service.update_task_status_from_agent.assert_called_once_with(
        task_id=task_id, new_status=status, agent_id=agent_id
    )


@pytest.mark.asyncio
async def test_report_task_status_from_agent_failure(
    client: TestClient, mock_task_service: AsyncMock
):
    """Test failure when reporting task status from an agent."""
    task_id = "test-task-uuid"
    agent_id = "ai-dev-agent"
    status = "invalid_status"

    mock_task_service.update_task_status_from_agent.return_value = (
        False,
        {"error": "Invalid status provided"},
    )

    response = client.post(
        f"/api/tasks/{task_id}/agent-status", json={"status": status, "agent_id": agent_id}
    )

    assert response.status_code == 400
    assert "Invalid status provided" in response.json()["detail"]
    mock_task_service.update_task_status_from_agent.assert_called_once_with(
        task_id=task_id, new_status=status, agent_id=agent_id
    )


@pytest.mark.asyncio
async def test_report_task_output_from_agent_success(
    client: TestClient, mock_task_service: AsyncMock
):
    """Test successful reporting of task output from an agent."""
    task_id = "test-task-uuid"
    agent_id = "ai-dev-agent"
    output_data = {"summary": "Generated code for auth module"}

    mock_task_service.save_agent_output.return_value = (
        True,
        {"task": {"id": task_id, "assignee": agent_id, "attachments": [output_data]}},
    )

    response = client.post(
        f"/api/tasks/{task_id}/agent-output", json={"output": output_data, "agent_id": agent_id}
    )

    assert response.status_code == 200
    assert response.json()["task"]["attachments"][0] == output_data
    mock_task_service.save_agent_output.assert_called_once_with(
        task_id=task_id, output=output_data, agent_id=agent_id
    )


@pytest.mark.asyncio
async def test_report_task_output_from_agent_failure(
    client: TestClient, mock_task_service: AsyncMock
):
    """Test failure when reporting task output from an agent."""
    task_id = "test-task-uuid"
    agent_id = "ai-dev-agent"
    output_data = {"error_reason": "Code generation failed"}

    mock_task_service.save_agent_output.return_value = (
        False,
        {"error": "Failed to store output"},
    )

    response = client.post(
        f"/api/tasks/{task_id}/agent-output", json={"output": output_data, "agent_id": agent_id}
    )

    assert response.status_code == 400
    assert "Failed to store output" in response.json()["detail"]
    mock_task_service.save_agent_output.assert_called_once_with(
        task_id=task_id, output=output_data, agent_id=agent_id
    )
