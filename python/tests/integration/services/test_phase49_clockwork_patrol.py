from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# CRITICAL: Import the service AFTER patching if possible, or patch the specific module reference
from server.services.scheduler_service import scheduler_service


@pytest.mark.asyncio
async def test_run_log_patrol_creates_task():
    """
    Test that Clockwork creates a task when errors are found.
    """
    mock_supabase = MagicMock()

    # Setup precise chain for archon_logs
    mock_logs_chain = MagicMock()
    mock_logs = [{"id": "log-1", "source": "api", "message": "500 Error", "level": "ERROR"}]
    # We must mock EVERY step of the chain to ensure .data is reached on the FINAL execute()
    mock_logs_chain.select.return_value.eq.return_value.gt.return_value.limit.return_value.execute.return_value.data = (
        mock_logs
    )

    # Setup precise chain for archon_projects
    mock_proj_chain = MagicMock()
    mock_proj_chain.select.return_value.limit.return_value.execute.return_value.data = [{"id": "proj-1"}]

    def table_side_effect(table_name):
        if table_name == "archon_logs":
            return mock_logs_chain
        return mock_proj_chain

    mock_supabase.table.side_effect = table_side_effect

    mock_task_service = AsyncMock()
    # Ensure it returns the tuple (success, result) as expected by the real service signature
    mock_task_service.create_task.return_value = (True, {"task": {"id": "task-repair-1", "assignee_id": "bcb00484-30bd-46fb-9e39-84b2ec4ced31"}})

    mock_agent_service = AsyncMock()

    # We patch BOTH possible paths to be absolutely sure
    with (
        patch("server.utils.get_supabase_client", return_value=mock_supabase),
        patch("server.services.projects.task_service.task_service", mock_task_service),
        patch("server.services.agent_service.agent_service", mock_agent_service),
    ):
        # Execute
        await scheduler_service._run_log_patrol()

        # Verify
        mock_task_service.create_task.assert_called_once()
        _, kwargs = mock_task_service.create_task.call_args
        assert kwargs["title"].startswith("Auto-Repair")
        assert "500 Error" in kwargs["description"]

        mock_agent_service.run_agent_task.assert_called_once()
        _, call_kwargs = mock_agent_service.run_agent_task.call_args
        assert call_kwargs.get("task_id") == "task-repair-1"
        assert call_kwargs.get("agent_id") == "bcb00484-30bd-46fb-9e39-84b2ec4ced31"


@pytest.mark.asyncio
async def test_run_log_patrol_no_errors():
    """
    Test that Clockwork does nothing if no errors found.
    """
    mock_supabase = MagicMock()
    # Mock empty logs chain
    mock_logs_chain = MagicMock()
    mock_logs_chain.select.return_value.eq.return_value.gt.return_value.limit.return_value.execute.return_value.data = []
    mock_supabase.table.return_value = mock_logs_chain

    mock_task_service = AsyncMock()

    with (
        patch("server.utils.get_supabase_client", return_value=mock_supabase),
        patch("server.services.projects.task_service.task_service", mock_task_service),
    ):
        await scheduler_service._run_log_patrol()

        mock_task_service.create_task.assert_not_called()
