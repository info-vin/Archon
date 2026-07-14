from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.report_service import report_service


@pytest.mark.asyncio
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.services.agent_service.agent_service", new_callable=AsyncMock)
@patch("src.server.repositories.base_repository.get_supabase_client")
@patch.object(report_service, "gather_report_context", new_callable=AsyncMock)
async def test_run_daily_executive_summary_success(mock_gather, mock_get_supabase, mock_agent_service, mock_task_service):
    """
    Test that daily executive summary creates a task with gathered context
    and dispatches a star-topology group chat task.
    """
    mock_gather.return_value = "Mocked Context for Daily"

    mock_supabase = MagicMock()
    report_service.supabase_client = mock_supabase

    mock_p_res = MagicMock()
    mock_p_res.data = [{"id": "test-project-123"}]
    mock_supabase.table().select().limit().execute.return_value = mock_p_res

    mock_task_service.create_task.return_value = (True, {"task": {"id": "test-task-123"}})

    await report_service.generate_daily_executive_summary()

    mock_gather.assert_awaited_once_with(1)
    mock_task_service.create_task.assert_awaited_once()

    call_kwargs = mock_task_service.create_task.call_args.kwargs
    assert call_kwargs["project_id"] == "test-project-123"
    assert "[Daily Report] Executive Summary" in call_kwargs["title"]
    assert "Mocked Context for Daily" in call_kwargs["description"]

    mock_supabase.table.assert_any_call("archon_logs")
    insert_call = [call for call in mock_supabase.table().insert.mock_calls if "report-service" in str(call)]
    assert len(insert_call) > 0
    payload = insert_call[0].args[0]
    assert "Daily Executive Summary group chat dispatched" in payload["message"]

@pytest.mark.asyncio
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.repositories.base_repository.get_supabase_client")
@patch("src.agents.workflow.engine_beta_graph.beta_graph", new_callable=AsyncMock)
@patch("src.server.services.text_to_speech_service.text_to_speech_service", new_callable=AsyncMock)
@patch("src.agents.nexus_oracle_agent.NexusOracleAgent.run", new_callable=AsyncMock)
@patch.object(report_service, "gather_report_context", new_callable=AsyncMock)
async def test_run_weekly_executive_summary_success(mock_gather, mock_oracle_run, mock_tts, mock_beta_graph, mock_get_supabase, mock_task_service):
    """
    Test that weekly executive summary executes Map-Reduce, Oracle, TTS, creates task,
    and updates status to done.
    """
    mock_gather.return_value = "Mocked Context for Weekly"
    
    class MockOracleData:
        health_score = 95
        system_status = "GREEN"
        main_bottleneck = "No issues"
        class MockTrends:
            monthly_budget_forecast = "Under budget"
            roi_trend = "Positive"
        long_term_trends = MockTrends()
        recommended_actions = []
        
    class MockOracleResult:
        data = MockOracleData()
    mock_oracle_run.return_value = MockOracleResult()

    class MockResult:
        def __init__(self, output):
            self.output = output
    mock_beta_graph.run.return_value = MockResult("Mocked Weekly Map-Reduce Output")
    
    mock_tts.generate_audio.return_value = "https://mock.supabase.co/storage/audio.mp3"

    mock_supabase = MagicMock()
    report_service.supabase_client = mock_supabase

    mock_p_res = MagicMock()
    mock_p_res.data = [{"id": "test-project-123"}]

    mock_c_res = MagicMock()
    mock_c_res.data = [{"id": "test-charlie-id"}]

    def mock_execute():
        return mock_p_res

    mock_supabase.table().select().limit().execute.return_value = mock_p_res
    mock_supabase.table().select().eq().execute.return_value = mock_c_res

    mock_task_service.create_task.return_value = (True, {"task": {"id": "test-task-weekly"}})
    mock_task_service.update_task = AsyncMock(return_value=(True, {}))

    await report_service.generate_weekly_executive_summary()

    mock_gather.assert_awaited_once_with(7)
    mock_oracle_run.assert_awaited_once()
    mock_beta_graph.run.assert_awaited_once()
    mock_tts.generate_audio.assert_awaited_once_with("Mocked Weekly Map-Reduce Output")
    mock_task_service.create_task.assert_awaited_once()
    mock_task_service.update_task.assert_awaited_once_with("test-task-weekly", {"status": "done"})

    # Check state injection
    state_arg = mock_beta_graph.run.call_args.kwargs["state"]
    prompt_content = state_arg.shared.messages[0]["content"]
    assert "Mocked Context for Weekly" in prompt_content
    assert "Nexus Oracle Insight" in prompt_content
    assert "95" in prompt_content
    assert "GREEN" in prompt_content

    call_kwargs = mock_task_service.create_task.call_args.kwargs
    assert "[Weekly Report] Executive Summary" in call_kwargs["title"]
    assert "Mocked Weekly Map-Reduce Output" in call_kwargs["description"]
    assert "🎧 **Listen to Podcast**: [Audio Link](https://mock.supabase.co/storage/audio.mp3)" in call_kwargs["description"]

@pytest.mark.asyncio
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.repositories.base_repository.get_supabase_client")
@patch("src.agents.workflow.engine_beta_graph.beta_graph", new_callable=AsyncMock)
@patch.object(report_service, "gather_report_context", new_callable=AsyncMock)
async def test_run_monthly_executive_summary_success(mock_gather, mock_beta_graph, mock_get_supabase, mock_task_service):
    """
    Test that monthly executive summary executes Map-Reduce, creates task,
    and updates status to done.
    """
    mock_gather.return_value = "Mocked Context for Monthly"

    class MockResult:
        def __init__(self, output):
            self.output = output
    mock_beta_graph.run.return_value = MockResult("Mocked Monthly Map-Reduce Output")

    mock_supabase = MagicMock()
    report_service.supabase_client = mock_supabase

    mock_p_res = MagicMock()
    mock_p_res.data = [{"id": "test-project-123"}]

    mock_c_res = MagicMock()
    mock_c_res.data = [{"id": "test-charlie-id"}]

    mock_supabase.table().select().limit().execute.return_value = mock_p_res
    mock_supabase.table().select().eq().execute.return_value = mock_c_res

    mock_task_service.create_task.return_value = (True, {"task": {"id": "test-task-monthly"}})
    mock_task_service.update_task = AsyncMock(return_value=(True, {}))

    await report_service.generate_monthly_executive_summary()

    mock_gather.assert_awaited_once_with(30)
    mock_beta_graph.run.assert_awaited_once()
    mock_task_service.create_task.assert_awaited_once()
    mock_task_service.update_task.assert_awaited_once_with("test-task-monthly", {"status": "done"})

    call_kwargs = mock_task_service.create_task.call_args.kwargs
    assert "[Monthly Report] Executive Summary" in call_kwargs["title"]
    assert "Mocked Monthly Map-Reduce Output" in call_kwargs["description"]

@pytest.mark.asyncio
@patch("src.server.repositories.base_repository.get_supabase_client")
async def test_gather_report_context_queries(mock_get_supabase):
    """
    Test that gather_report_context correctly constructs and executes queries
    on leads, token_usage, archon_logs, and archon_tasks.
    """
    mock_supabase = MagicMock()
    report_service.supabase_client = mock_supabase

    mock_res_leads = MagicMock()
    mock_res_leads.data = [{"company_name": "Google", "job_title": "SWE", "status": "active"}]

    mock_res_token = MagicMock()
    mock_res_token.data = [{"input_tokens": 100, "output_tokens": 200, "cost_usd": 0.005}]

    mock_res_logs = MagicMock()
    mock_res_logs.data = [{"level": "ERROR", "source": "test-src", "message": "Test error message", "created_at": "2026-05-22"}]

    mock_res_tasks = MagicMock()
    mock_res_tasks.data = [{"title": "Task A", "status": "doing", "assignee": "Alice"}]

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

    result = await report_service.gather_report_context(5)

    assert "Google (SWE) -> active" in result
    assert "Input Tokens: 100" in result
    assert "Output Tokens: 200" in result
    assert "Total Cost: $0.0050 USD" in result
    assert "[ERROR] test-src: Test error message" in result
    assert "Task A (Alice) -> status: doing" in result
