from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.scheduler.jobs.business import run_daily_executive_summary


@pytest.mark.asyncio
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.services.scheduler.jobs.business.get_supabase_client")
@patch("src.agents.workflow.engine_beta_graph.beta_graph", new_callable=AsyncMock)
async def test_run_daily_executive_summary_success(mock_beta_graph, mock_get_supabase, mock_task_service):
    """
    Test that the executive summary task correctly executes the beta graph,
    creates a task, and logs the ROI correctly.
    """
    # 1. Setup Graph Mock
    class MockResult:
        def __init__(self, output):
            self.output = output

    mock_beta_graph.run.return_value = MockResult("Mocked Executive Summary")

    # 2. Setup DB Mock
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    # Mock project fetch
    mock_p_res = MagicMock()
    mock_p_res.data = [{"id": "test-project-123"}]
    mock_supabase.table().select().limit().execute.return_value = mock_p_res

    # 3. Setup Task Service Mock
    mock_task_service.create_task.return_value = (True, {"task": {"id": "test-task-123"}})

    # --- Execute ---
    await run_daily_executive_summary()

    # --- Assertions ---
    # Graph was called
    mock_beta_graph.run.assert_awaited_once()

    # Task was created
    mock_task_service.create_task.assert_awaited_once()
    call_kwargs = mock_task_service.create_task.call_args.kwargs
    assert call_kwargs["project_id"] == "test-project-123"
    assert "[Daily Report] Executive Summary" in call_kwargs["title"]
    assert "Mocked Executive Summary" in call_kwargs["description"]

    # Log was inserted
    mock_supabase.table.assert_any_call("archon_logs")
    # Verify the log insertion args
    insert_call = [call for call in mock_supabase.table().insert.mock_calls if "clockwork-scheduler" in str(call)]
    assert len(insert_call) > 0
    payload = insert_call[0].args[0]
    assert "Daily Executive Summary completed" in payload["message"]
    assert payload["details"]["type"] == "executive_summary"
