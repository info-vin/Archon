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


@pytest.mark.asyncio
@patch("src.server.services.report_service.report_service.send_summary_telegram", new_callable=AsyncMock)
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.services.agent_service.AgentService._award_agent_xp", new_callable=AsyncMock)
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_workflow_engine_dispatches_telegram_on_daily_summary_completion(
    mock_post, mock_award_xp, mock_task_service, mock_send_telegram
):
    from unittest.mock import MagicMock

    from src.server.services.shared_constants import TaskFeatureEnum

    task_id = "test-task-daily"
    agent_id = AgentUUIDs.SUPERVISOR
    mock_task_data = {
        "id": task_id,
        "title": "[Daily] Executive Summary",
        "description": "Daily details",
        "feature": TaskFeatureEnum.DAILY_EXECUTIVE_SUMMARY,
    }

    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "success": True,
        "result": "Charlie's complete summary",
        "metadata": {"messages": [], "step_count": 2},
    }
    resp.raise_for_status = MagicMock()
    mock_post.return_value = resp

    agent_service = AgentService()
    await agent_service._run_workflow_engine_task(task_id, mock_task_data, agent_id)

    mock_send_telegram.assert_awaited_once_with(
        title_prefix="Daily",
        content="Charlie's complete summary",
        task_id=task_id,
    )


@pytest.mark.asyncio
@patch("src.server.services.report_service.report_service.send_summary_telegram", new_callable=AsyncMock)
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.services.agent_service.AgentService._award_agent_xp", new_callable=AsyncMock)
@patch("httpx.AsyncClient.post", new_callable=AsyncMock)
async def test_workflow_engine_fallback_telegram_on_failure(
    mock_post, mock_award_xp, mock_task_service, mock_send_telegram
):
    from unittest.mock import MagicMock

    from src.server.services.shared_constants import TaskFeatureEnum

    task_id = "test-task-daily-fail"
    agent_id = AgentUUIDs.SUPERVISOR
    mock_task_data = {
        "id": task_id,
        "title": "[Daily] Executive Summary",
        "description": "Raw daily metrics",
        "feature": TaskFeatureEnum.DAILY_EXECUTIVE_SUMMARY,
    }

    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "success": False,
        "error": "Circuit Breaker Tripped",
    }
    resp.raise_for_status = MagicMock()
    mock_post.return_value = resp

    agent_service = AgentService()
    await agent_service._run_workflow_engine_task(task_id, mock_task_data, agent_id)

    # Must verify fallback telegram was called
    mock_send_telegram.assert_awaited_once()
    assert mock_send_telegram.call_args.kwargs["title_prefix"] == "Daily (Fallback)"
    assert "Raw daily metrics" in mock_send_telegram.call_args.kwargs["content"]
    assert mock_send_telegram.call_args.kwargs["task_id"] == task_id
