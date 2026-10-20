from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.report_service import report_service


@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.services.agent_service.agent_service", new_callable=AsyncMock)
@patch("src.server.repositories.base_repository.get_supabase_client")
@patch.object(report_service, "gather_report_context", new_callable=AsyncMock)
async def test_run_daily_executive_summary_success(mock_gather, mock_get_supabase, mock_agent_service, mock_task_service, mock_send_telegram):
    """
    Test that daily executive summary creates a task with gathered context
    and dispatches a star-topology group chat task without premature Telegram dispatch.
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
    assert "[Daily] Executive Summary" in call_kwargs["title"]
    assert "Mocked Context for Daily" in call_kwargs["description"]

    # Verify Telegram notification is NOT prematurely sent before Agent completes
    mock_send_telegram.assert_not_awaited()

    mock_supabase.table.assert_any_call("archon_logs")
    insert_call = [call for call in mock_supabase.table().insert.mock_calls if "report-service" in str(call)]
    assert len(insert_call) > 0
    payload = insert_call[0].args[0]
    assert "Daily Executive Summary processed. Task" in payload["message"]

@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.repositories.base_repository.get_supabase_client")
@patch("src.server.utils.get_supabase_client")
@patch("src.agents.workflow.engine_beta_graph.beta_graph", new_callable=AsyncMock)
@patch("src.server.services.text_to_speech_service.text_to_speech_service", new_callable=AsyncMock)
@patch("src.agents.nexus_oracle_agent.NexusOracleAgent.run", new_callable=AsyncMock)
@patch.object(report_service, "gather_report_context", new_callable=AsyncMock)
async def test_run_weekly_executive_summary_success(
    mock_gather,
    mock_oracle_run,
    mock_tts,
    mock_beta_graph,
    mock_utils_supabase,
    mock_get_supabase,
    mock_task_service,
    mock_send_telegram,
):
    """
    Test that weekly executive summary executes Map-Reduce, Oracle, TTS, creates task,
    updates status to done, and dispatches full summary content to Telegram.
    """
    mock_send_telegram.return_value = True
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

    mock_oracle_run.return_value = MockOracleData()

    class MockResult:
        def __init__(self, output):
            self.output = output
    mock_beta_graph.run.return_value = MockResult("Mocked Weekly Map-Reduce Output")

    # Fix: generate_audio now returns a tuple (success, result_bytes)
    mock_tts.generate_audio.return_value = (True, b"mock_audio_bytes")

    mock_supabase = MagicMock()
    report_service.supabase_client = mock_supabase

    # Fix: Mock the enrichment service's supabase client and its storage upload
    mock_enrichment_sb = MagicMock()
    mock_utils_supabase.return_value = mock_enrichment_sb
    mock_enrichment_sb.storage.from_().create_signed_url.return_value = {"signedURL": "https://mock.supabase.co/storage/audio.wav"}

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
    assert "[Weekly] Executive Summary" in call_kwargs["title"]
    assert "Mocked Weekly Map-Reduce Output" in call_kwargs["description"]
    assert "🎧 **Listen to Podcast**: [Audio Link](https://mock.supabase.co/storage/audio.wav)" in call_kwargs["description"]

    # Verify Telegram notification contains full body, not a truncated snippet
    mock_send_telegram.assert_awaited_once()
    tg_msg = mock_send_telegram.call_args[0][0]
    assert "Mocked Weekly Map-Reduce Output" in tg_msg
    assert "🎧 **Listen to Podcast**: [Audio Link](https://mock.supabase.co/storage/audio.wav)" in tg_msg
    assert "星環 Weekly 已產出" in tg_msg
    assert "👉 完整數據與儀表板請至 Admin UI 查看" in tg_msg

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
    assert "[Monthly] Executive Summary" in call_kwargs["title"]
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
    assert "[ERROR] test-src: `Test error message`" in result
    assert "Task A (Alice) -> status: doing" in result


@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
async def test_send_summary_telegram_direct(mock_send_telegram):
    mock_send_telegram.return_value = True
    success = await report_service.send_summary_telegram(
        title_prefix="Daily",
        content="Charlie's summarized insights",
        task_id="test-task-123",
    )
    assert success is True
    mock_send_telegram.assert_awaited_once()
    msg = mock_send_telegram.call_args[0][0]
    assert "星環 Daily 已產出" in msg
    assert "Charlie's summarized insights" in msg
    assert "taskId=test-task-123" in msg


def test_get_logs_context_aggregation_and_sanitization():
    mock_supabase = MagicMock()
    mock_res = MagicMock()
    mock_res.data = [
        {"level": "ALERT", "source": "RateLimitHandler", "message": "Rate limit hit: 429\nStacktrace line 2", "created_at": "2026-10-18T10:00:00Z"},
        {"level": "ALERT", "source": "RateLimitHandler", "message": "Rate limit hit: 429\nStacktrace line 2", "created_at": "2026-10-18T10:01:00Z"},
        {"level": "ERROR", "source": "system-telegram", "message": "HTTP 400 Bad Request: can't parse", "created_at": "2026-10-18T10:02:00Z"},
    ]
    mock_supabase.table().select().gt().in_().execute.return_value = mock_res
    report_service.supabase_client = mock_supabase

    ctx = report_service._get_logs_context("2026-10-18T00:00:00Z")
    assert "Total Alerts/Errors: 3" in ctx
    assert "(x2)" in ctx
    assert "`Rate limit hit: 429`" in ctx
    assert "`HTTP 400 Bad Request: can't parse`" in ctx
    assert "\nStacktrace" not in ctx  # Multi-line trace was stripped


@pytest.mark.asyncio
@patch.object(report_service, "_create_summary_task_and_log", new_callable=AsyncMock)
@patch("src.server.services.report_enrichment_service.report_enrichment_service.attach_podcast_audio", new_callable=AsyncMock)
@patch("src.server.services.report_enrichment_service.report_enrichment_service.inject_nexus_oracle_insights", new_callable=AsyncMock)
@patch("src.server.services.prompt_service.prompt_service.get_prompt")
@patch("src.server.services.settings_service.SettingsService.get_all_settings")
@patch("src.agents.workflow.engine_beta_graph.beta_graph", new_callable=AsyncMock)
@patch.object(report_service, "gather_report_context", new_callable=AsyncMock)
async def test_execute_map_reduce_summary_with_management_steering_focus(
    mock_gather,
    mock_beta_graph,
    mock_get_settings,
    mock_get_prompt,
    mock_inject_oracle,
    mock_attach_audio,
    mock_create_task_log,
):
    """
    Test that management_steering_focus from SchedulerConfig is injected into
    the Map-Reduce context when present.
    """
    mock_gather.return_value = "Base Report Context"
    mock_inject_oracle.side_effect = lambda c: c
    mock_attach_audio.side_effect = lambda t: t
    mock_get_prompt.return_value = "Prompt Template: {context_md}"
    mock_get_settings.return_value = {
        "MANAGEMENT_STEERING_FOCUS": "本週重點驗證金融業潛客轉化率與 429 降噪成效"
    }

    class MockResult:
        def __init__(self, output):
            self.output = output
    mock_beta_graph.run.return_value = MockResult("Summary Output")

    await report_service._execute_map_reduce_summary(7, "Weekly", "WEEKLY_EXECUTIVE_SUMMARY")

    state_arg = mock_beta_graph.run.call_args.kwargs["state"]
    prompt_content = state_arg.shared.messages[0]["content"]
    assert "Base Report Context" in prompt_content
    assert "### 🎯 管理者戰略關注焦點 (Management Steering Focus)" in prompt_content
    assert "本週重點驗證金融業潛客轉化率與 429 降噪成效" in prompt_content


@pytest.mark.asyncio
@patch.object(report_service, "_create_summary_task_and_log", new_callable=AsyncMock)
@patch("src.server.services.report_enrichment_service.report_enrichment_service.attach_podcast_audio", new_callable=AsyncMock)
@patch("src.server.services.report_enrichment_service.report_enrichment_service.inject_nexus_oracle_insights", new_callable=AsyncMock)
@patch("src.server.services.prompt_service.prompt_service.get_prompt")
@patch("src.server.services.settings_service.SettingsService.get_all_settings")
@patch("src.agents.workflow.engine_beta_graph.beta_graph", new_callable=AsyncMock)
@patch.object(report_service, "gather_report_context", new_callable=AsyncMock)
async def test_execute_map_reduce_summary_without_management_steering_focus(
    mock_gather,
    mock_beta_graph,
    mock_get_settings,
    mock_get_prompt,
    mock_inject_oracle,
    mock_attach_audio,
    mock_create_task_log,
):
    """
    Test that when management_steering_focus is not set, no steering header is injected.
    """
    mock_gather.return_value = "Base Report Context"
    mock_inject_oracle.side_effect = lambda c: c
    mock_attach_audio.side_effect = lambda t: t
    mock_get_prompt.return_value = "Prompt Template: {context_md}"
    mock_get_settings.return_value = {}

    class MockResult:
        def __init__(self, output):
            self.output = output
    mock_beta_graph.run.return_value = MockResult("Summary Output")

    await report_service._execute_map_reduce_summary(7, "Weekly", "WEEKLY_EXECUTIVE_SUMMARY")

    state_arg = mock_beta_graph.run.call_args.kwargs["state"]
    prompt_content = state_arg.shared.messages[0]["content"]
    assert "Base Report Context" in prompt_content
    assert "### 🎯 管理者戰略關注焦點" not in prompt_content



