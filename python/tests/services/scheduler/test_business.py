from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.scheduler.jobs.business import (
    gather_report_context,
    run_daily_executive_summary,
    run_monthly_executive_summary,
    run_weekly_executive_summary,
)


@pytest.mark.asyncio
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.services.agent_service.agent_service", new_callable=AsyncMock)
@patch("src.server.services.scheduler.jobs.business.get_supabase_client")
@patch("src.server.services.scheduler.jobs.business.gather_report_context", new_callable=AsyncMock)
async def test_run_daily_executive_summary_success(mock_gather, mock_get_supabase, mock_agent_service, mock_task_service):
    """
    Test that daily executive summary creates a task with gathered context
    and dispatches a star-topology group chat task.
    """
    # 1. Setup Mock context
    mock_gather.return_value = "Mocked Context for Daily"

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
    mock_gather.assert_awaited_once_with(1)
    mock_task_service.create_task.assert_awaited_once()

    call_kwargs = mock_task_service.create_task.call_args.kwargs
    assert call_kwargs["project_id"] == "test-project-123"
    assert "[Daily Report] Executive Summary" in call_kwargs["title"]
    assert "Mocked Context for Daily" in call_kwargs["description"]

    # Log was inserted to track dispatch
    mock_supabase.table.assert_any_call("archon_logs")
    insert_call = [call for call in mock_supabase.table().insert.mock_calls if "clockwork-scheduler" in str(call)]
    assert len(insert_call) > 0
    payload = insert_call[0].args[0]
    assert "Daily Executive Summary group chat dispatched" in payload["message"]


@pytest.mark.asyncio
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.services.scheduler.jobs.business.get_supabase_client")
@patch("src.agents.workflow.engine_beta_graph.beta_graph", new_callable=AsyncMock)
@patch("src.server.services.scheduler.jobs.business.gather_report_context", new_callable=AsyncMock)
async def test_run_weekly_executive_summary_success(mock_gather, mock_beta_graph, mock_get_supabase, mock_task_service):
    """
    Test that weekly executive summary executes Map-Reduce, creates task,
    and updates status to done.
    """
    # 1. Setup Mock context
    mock_gather.return_value = "Mocked Context for Weekly"

    # 2. Setup Graph Mock
    class MockResult:
        def __init__(self, output):
            self.output = output
    mock_beta_graph.run.return_value = MockResult("Mocked Weekly Map-Reduce Output")

    # 3. Setup DB Mock
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    # Mock project fetch
    mock_p_res = MagicMock()
    mock_p_res.data = [{"id": "test-project-123"}]
    mock_supabase.table().select().limit().execute.return_value = mock_p_res

    # 4. Setup Task Service Mock
    mock_task_service.create_task.return_value = (True, {"task": {"id": "test-task-weekly"}})
    mock_task_service.update_task = AsyncMock(return_value=(True, {}))

    # --- Execute ---
    await run_weekly_executive_summary()

    # --- Assertions ---
    mock_gather.assert_awaited_once_with(7)
    mock_beta_graph.run.assert_awaited_once()
    mock_task_service.create_task.assert_awaited_once()
    mock_task_service.update_task.assert_awaited_once_with("test-task-weekly", {"status": "done"})

    call_kwargs = mock_task_service.create_task.call_args.kwargs
    assert "[Weekly Report] Executive Summary" in call_kwargs["title"]
    assert "Mocked Weekly Map-Reduce Output" in call_kwargs["description"]


@pytest.mark.asyncio
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.services.scheduler.jobs.business.get_supabase_client")
@patch("src.agents.workflow.engine_beta_graph.beta_graph", new_callable=AsyncMock)
@patch("src.server.services.scheduler.jobs.business.gather_report_context", new_callable=AsyncMock)
async def test_run_monthly_executive_summary_success(mock_gather, mock_beta_graph, mock_get_supabase, mock_task_service):
    """
    Test that monthly executive summary executes Map-Reduce, creates task,
    and updates status to done.
    """
    # 1. Setup Mock context
    mock_gather.return_value = "Mocked Context for Monthly"

    # 2. Setup Graph Mock
    class MockResult:
        def __init__(self, output):
            self.output = output
    mock_beta_graph.run.return_value = MockResult("Mocked Monthly Map-Reduce Output")

    # 3. Setup DB Mock
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    # Mock project fetch
    mock_p_res = MagicMock()
    mock_p_res.data = [{"id": "test-project-123"}]
    mock_supabase.table().select().limit().execute.return_value = mock_p_res

    # 4. Setup Task Service Mock
    mock_task_service.create_task.return_value = (True, {"task": {"id": "test-task-monthly"}})
    mock_task_service.update_task = AsyncMock(return_value=(True, {}))

    # --- Execute ---
    await run_monthly_executive_summary()

    # --- Assertions ---
    mock_gather.assert_awaited_once_with(30)
    mock_beta_graph.run.assert_awaited_once()
    mock_task_service.create_task.assert_awaited_once()
    mock_task_service.update_task.assert_awaited_once_with("test-task-monthly", {"status": "done"})

    call_kwargs = mock_task_service.create_task.call_args.kwargs
    assert "[Monthly Report] Executive Summary" in call_kwargs["title"]
    assert "Mocked Monthly Map-Reduce Output" in call_kwargs["description"]


@pytest.mark.asyncio
@patch("src.server.services.scheduler.jobs.business.get_supabase_client")
async def test_gather_report_context_queries(mock_get_supabase):
    """
    Test that gather_report_context correctly constructs and executes queries
    on leads, token_usage, archon_logs, and archon_tasks.
    """
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    # Mock return values for all select queries
    mock_res_leads = MagicMock()
    mock_res_leads.data = [{"company_name": "Google", "job_title": "SWE", "status": "active"}]

    mock_res_token = MagicMock()
    mock_res_token.data = [{"input_tokens": 100, "output_tokens": 200, "cost_usd": 0.005}]

    mock_res_logs = MagicMock()
    mock_res_logs.data = [{"level": "ERROR", "source": "test-src", "message": "Test error message", "created_at": "2026-05-22"}]

    mock_res_tasks = MagicMock()
    mock_res_tasks.data = [{"title": "Task A", "status": "doing", "assignee": "Alice"}]

    # A mock query chain helper to return our mocked responses in order
    def mock_table(table_name):
        table_mock = MagicMock()
        if table_name == "leads":
            table_mock.select.return_value.gt.return_value.execute.return_value = mock_res_leads
        elif table_name == "token_usage":
            table_mock.select.return_value.gt.return_value.execute.return_value = mock_res_token
        elif table_name == "archon_logs":
            table_mock.select.return_value.gt.return_value.in_.return_value.execute.return_value = mock_res_logs
        elif table_name == "archon_tasks":
            table_mock.select.return_value.gt.return_value.execute.return_value = mock_res_tasks
        return table_mock

    mock_supabase.table.side_effect = mock_table

    result = await gather_report_context(5)

    assert "Google (SWE) -> active" in result
    assert "Input Tokens: 100" in result
    assert "Output Tokens: 200" in result
    assert "Total Cost: $0.0050 USD" in result
    assert "[ERROR] test-src: Test error message" in result
    assert "Task A (Alice) -> status: doing" in result
