from unittest.mock import AsyncMock, patch

import pytest

from src.server.services.agent_service import AgentService
from src.server.services.shared_constants import AgentUUIDs


@pytest.mark.asyncio
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch.object(AgentService, "_run_workflow_engine_task", new_callable=AsyncMock)
async def test_supervisor_routes_to_workflow_engine(mock_workflow_engine, mock_task_service):
    """
    Anti-Ghost Development Test (Phase 5.0.2):
    Physically verifies that when _run_general_agent_task is called with the Supervisor UUID,
    it strictly routes the execution to _run_workflow_engine_task and returns early,
    preventing fallback to the legacy single-agent LLM logic.
    """
    # Arrange
    task_id = "test-task-123"
    agent_id = AgentUUIDs.SUPERVISOR
    mock_task_data = {"id": task_id, "title": "Test Marketing Data", "description": "Need stats"}

    # Mock task_service.get_task to return our fake task
    mock_task_service.get_task.return_value = (True, {"task": mock_task_data})

    agent_service = AgentService()

    # Act
    await agent_service._run_general_agent_task(task_id, agent_id)

    # Assert
    mock_workflow_engine.assert_awaited_once_with(task_id, mock_task_data, agent_id)
