from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# CRITICAL: Import the service AFTER patching if possible, or patch the specific module reference
from src.server.services.scheduler_service import scheduler_service


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

    mock_self_tuning_service = AsyncMock()
    mock_self_tuning_service.tune_prompt_from_error.return_value = {"success": True, "proposal_id": "prop-1"}

    # We patch ALL possible paths to be absolutely sure
    with (
        patch("src.server.utils.get_supabase_client", return_value=mock_supabase),
        patch("src.server.services.projects.task_service.task_service", mock_task_service),
        patch("src.server.services.agent_service.agent_service", mock_agent_service),
        patch("src.server.services.system.self_tuning_service.self_tuning_service", mock_self_tuning_service),
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

        mock_self_tuning_service.tune_prompt_from_error.assert_called_once_with("log-1")


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
        patch("src.server.utils.get_supabase_client", return_value=mock_supabase),
        patch("src.server.services.projects.task_service.task_service", mock_task_service),
    ):
        await scheduler_service._run_log_patrol()

        mock_task_service.create_task.assert_not_called()


@pytest.mark.asyncio
async def test_model_verification_sleep_mode():
    """
    Test that model verification probe skips verification and logs Sleep Mode when HF is asleep.
    """
    mock_supabase = MagicMock()
    mock_logs_chain = MagicMock()
    mock_supabase.table.return_value = mock_logs_chain

    with (
        patch("src.server.services.scheduler.jobs.patrol.is_hf_awake", return_value=False),
        patch("src.server.utils.get_supabase_client", return_value=mock_supabase),
    ):
        await scheduler_service._run_model_verification()

        # Check that we inserted a log
        mock_supabase.table.assert_called_with("archon_logs")
        mock_logs_chain.insert.assert_called_once()
        args, _ = mock_logs_chain.insert.call_args
        payload = args[0]
        assert payload["source"] == "clockwork-scheduler"
        assert payload["level"] == "INFO"
        assert "[Sleep Mode]" in payload["message"]


@pytest.mark.asyncio
async def test_run_ssot_audit_detects_hardcoding(tmp_path, monkeypatch):
    """
    Test that SSOT Audit detects hardcoded models and network hosts, creating a task.
    """
    mock_supabase = MagicMock()

    mock_proj_chain = MagicMock()
    mock_proj_chain.select.return_value.limit.return_value.execute.return_value.data = [{"id": "proj-1"}]
    mock_supabase.table.return_value = mock_proj_chain

    mock_task_service = AsyncMock()
    mock_task_service.create_task.return_value = (True, {"task": {"id": "task-ssot-1", "assignee_id": "devbot"}})

    mock_agent_service = AsyncMock()

    # Create dummy files to trigger warnings
    src_dir = tmp_path / "python" / "src"
    src_dir.mkdir(parents=True)

    # 1. Hardcoded gemini
    bad_file = src_dir / "bad.py"
    bad_file.write_text("model = 'gemini-3.1-flash-lite'")

    # 2. Hardcoded mcp
    bad_network = src_dir / "bad_net.py"
    bad_network.write_text("url = 'http://archon-mcp:8000'")

    from src.server.services.scheduler.jobs.tech_debt_patrol import run_ssot_audit

    monkeypatch.chdir(tmp_path)

    with (
        patch("src.server.utils.get_supabase_client", return_value=mock_supabase),
        patch("src.server.services.projects.task_service.task_service", mock_task_service),
        patch("src.server.services.agent_service.agent_service", mock_agent_service),
    ):

        await run_ssot_audit()

        # Verify
        mock_task_service.create_task.assert_called_once()
        _, kwargs = mock_task_service.create_task.call_args
        assert "Auto-Cleanup: SSOT Hardcoding Audit" in kwargs["title"]
        assert "gemini-3" in kwargs["description"]
        assert "archon-mcp" in kwargs["description"]

        mock_agent_service.run_agent_task.assert_called_once()
