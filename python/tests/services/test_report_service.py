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
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
@patch("src.server.repositories.base_repository.get_supabase_client")
@patch("src.agents.workflow.engine_beta_graph.beta_graph", new_callable=AsyncMock)
@patch.object(report_service, "gather_report_context", new_callable=AsyncMock)
async def test_run_monthly_executive_summary_success(
    mock_gather, mock_beta_graph, mock_get_supabase, mock_task_service, mock_send_telegram
):
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
@patch("src.server.services.report_enrichment_service.report_enrichment_service.dispatch_dual_voice_briefings", new_callable=AsyncMock)
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
async def test_send_summary_telegram_direct(mock_send_telegram, mock_dispatch_voice):
    mock_send_telegram.return_value = True
    mock_dispatch_voice.return_value = []
    success = await report_service.send_summary_telegram(
        title_prefix="Daily",
        content="Charlie's summarized insights",
        task_id="test-task-123",
    )
    assert success is True
    mock_send_telegram.assert_awaited_once()
    mock_dispatch_voice.assert_awaited_once_with("Charlie's summarized insights")
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


def test_get_leads_context_enrichment_with_qualified_pool_and_blogs():
    """
    Verify _get_leads_context includes lead scores, pain points, active qualified leads pool,
    and Bob's marketing blog pipeline so the daily summary has concrete business substance.
    """
    mock_supabase = MagicMock()
    report_service.supabase_client = mock_supabase

    new_leads_res = MagicMock(
        data=[
            {
                "company_name": "樸真國際股份有限公司",
                "job_title": "AI 應用工程師",
                "status": "qualified",
                "enrichment_score": 74,
                "identified_need": "工廠流程自動化 × 中台系統整合",
            }
        ]
    )
    qualified_pool_res = MagicMock(
        data=[
            {
                "company_name": "潤御開發有限公司",
                "job_title": "兼職 AI 應用開發工程師",
                "status": "qualified",
                "enrichment_score": 74,
                "identified_need": "OpenAI API / LLM / RAG 知識庫建置",
            }
        ]
    )
    blogs_res = MagicMock(
        data=[
            {
                "title": "🚀 AI狂潮席捲傳統產業！",
                "status": "draft",
                "ai_score": 85,
            }
        ]
    )

    def mock_table(name: str):
        t = MagicMock()
        if name == "leads":
            t.select.return_value.gt.return_value.execute.return_value = new_leads_res
            t.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = (
                qualified_pool_res
            )
        elif name == "blog_posts":
            t.select.return_value.order.return_value.limit.return_value.execute.return_value = blogs_res
        return t

    mock_supabase.table.side_effect = mock_table

    summary = report_service._get_leads_context("2026-10-23T00:00:00Z")
    assert "樸真國際股份有限公司 (AI 應用工程師) -> qualified [Score: 74]" in summary
    assert "痛點: 工廠流程自動化 × 中台系統整合" in summary
    assert "Active Qualified Leads Pool" in summary
    assert "潤御開發有限公司" in summary
    assert "Marketing Content Pipeline" in summary
    assert "🚀 AI狂潮席捲傳統產業！ -> status: draft [AI Score: 85]" in summary


@pytest.mark.asyncio
@patch("src.server.services.report_enrichment_service.asyncio.sleep", new_callable=AsyncMock)
@patch("src.server.services.report_enrichment_service.ReportEnrichmentService._generate_script_with_llm", new_callable=AsyncMock)
@patch("src.server.services.text_to_speech_service.text_to_speech_service.generate_audio", new_callable=AsyncMock)
@patch("src.server.services.system.telegram_service.telegram_service.send_voice", new_callable=AsyncMock)
@patch("src.server.utils.get_supabase_client")
async def test_dispatch_dual_voice_briefings_zh_and_en(
    mock_get_supabase,
    mock_send_voice,
    mock_generate_audio,
    mock_gen_script,
    mock_sleep,
):
    """
    Verify dispatch_dual_voice_briefings produces 2 distinct Telegram voice bubbles:
    1. Mandarin Executive Brief (Puck voice)
    2. English CNN Business Flash Briefing (Fenrir voice)
    with a 5-second rate-limit pause in between.
    """
    from src.server.services.report_enrichment_service import report_enrichment_service

    mock_gen_script.side_effect = [
        "各位早安，今日業務線新增潤御開發等合格潛客，請優先跟進。",
        "Good morning. This is your Archon Executive Intelligence Briefing. Stay sharp.",
    ]
    mock_generate_audio.side_effect = [
        (True, b"WAV_ZH_BYTES"),
        (True, b"WAV_EN_BYTES"),
    ]
    mock_send_voice.return_value = True

    mock_sb = MagicMock()
    mock_sb.storage.from_.return_value.create_signed_url.return_value = {
        "signedURL": "https://supabase.test/podcast.wav"
    }
    mock_get_supabase.return_value = mock_sb

    urls = await report_enrichment_service.dispatch_dual_voice_briefings("Full Executive Summary Markdown")

    assert len(urls) == 2
    assert mock_generate_audio.await_count == 2
    assert mock_generate_audio.call_args_list[0].kwargs["voice_name"] == "Puck"
    assert mock_generate_audio.call_args_list[1].kwargs["voice_name"] == "Fenrir"

    assert mock_send_voice.await_count == 2
    assert "執行長重點語音速報" in mock_send_voice.call_args_list[0].kwargs["caption"]
    assert "CNN Business Flash" in mock_send_voice.call_args_list[1].kwargs["caption"]
    mock_sleep.assert_awaited_once_with(5.0)


@pytest.mark.asyncio
@patch("src.server.services.report_enrichment_service.ReportEnrichmentService._generate_script_with_llm", new_callable=AsyncMock)
@patch("src.server.services.text_to_speech_service.text_to_speech_service.generate_audio", new_callable=AsyncMock)
@patch("src.server.services.system.telegram_service.telegram_service.send_voice", new_callable=AsyncMock)
@patch("src.server.utils.get_supabase_client")
async def test_trigger_emergency_voice_alert_respects_daily_cap(
    mock_get_supabase,
    mock_send_voice,
    mock_generate_audio,
    mock_gen_script,
):
    """Verify emergency voice alert sends voice bubble when under cap and blocks when >= 3 today."""
    from src.server.services.report_enrichment_service import report_enrichment_service

    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = MagicMock(
        data=[{"id": 1}]
    )
    mock_get_supabase.return_value = mock_sb
    mock_gen_script.return_value = "Archon 系統緊急告警，請立即查閱。"
    mock_generate_audio.return_value = (True, b"WAV_EMERGENCY_BYTES")
    mock_send_voice.return_value = True

    res = await report_enrichment_service.trigger_emergency_voice_alert("Circuit Breaker Tripped")
    assert res is True
    mock_send_voice.assert_awaited_once()

    # Now simulate cap reached (3 alerts already logged today)
    mock_send_voice.reset_mock()
    mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = MagicMock(
        data=[{"id": 1}, {"id": 2}, {"id": 3}]
    )
    res_capped = await report_enrichment_service.trigger_emergency_voice_alert("Another failure")
    assert res_capped is False
    mock_send_voice.assert_not_awaited()


@pytest.mark.asyncio
@patch("src.server.services.report_enrichment_service.report_enrichment_service.trigger_emergency_voice_alert", new_callable=AsyncMock)
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
async def test_send_summary_telegram_fallback_triggers_emergency_voice(mock_send_telegram, mock_trigger_emergency):
    """Verify send_summary_telegram triggers emergency voice alert when title_prefix contains 'Fallback'."""
    mock_send_telegram.return_value = True
    mock_trigger_emergency.return_value = True
    success = await report_service.send_summary_telegram(
        title_prefix="Daily (Fallback)",
        content="⚠️ 多 Agent 協同討論未能在時限內收斂",
        task_id="test-fallback-999",
    )
    assert success is True
    mock_send_telegram.assert_awaited_once()
    mock_trigger_emergency.assert_awaited_once_with("⚠️ 多 Agent 協同討論未能在時限內收斂")


@pytest.mark.asyncio
@patch("src.server.services.token_usage_service.TokenUsageService.log_usage", new_callable=AsyncMock)
@patch("src.server.services.credential_service.credential_service.get_credential", new_callable=AsyncMock)
@patch("google.genai.Client")
async def test_generate_script_with_llm_model_fallback_and_token_logging(
    mock_genai_client, mock_get_cred, mock_log_usage
):
    """
    Verify _generate_script_with_llm:
    1. Tries SUPERVISOR_MODEL (gemini-3.6-flash) first; if it raises 429, degrades to DEFAULT_PRO (gemini-3.5-flash-lite).
    2. Strips markdown symbols (*_`#[]) and logs token usage via TokenUsageService.log_usage.
    3. Provides clean English anchor fallback if all models fail on DAILY_VOICE_BRIEF_EN.
    """
    from src.server.services.report_enrichment_service import ReportEnrichmentService

    mock_get_cred.side_effect = ["key-primary", "key-primary"]

    mock_ok_resp = MagicMock()
    mock_ok_resp.text = "**Good morning!** [CNN] `#Flash` _Update_"
    mock_ok_resp.usage_metadata = MagicMock(prompt_token_count=120, candidates_token_count=45)

    mock_instance = mock_genai_client.return_value
    # 1st model (gemini-3.6-flash) raises 429, 2nd model (gemini-3.5-flash-lite) succeeds
    mock_instance.aio.models.generate_content = AsyncMock(
        side_effect=[Exception("429 Quota exceeded"), mock_ok_resp]
    )

    script = await ReportEnrichmentService._generate_script_with_llm(
        "DAILY_VOICE_BRIEF_EN", "Prompt instruction", "Raw summary markdown"
    )
    assert script == "Good morning! CNN Flash Update"
    assert mock_instance.aio.models.generate_content.await_count == 2
    assert mock_instance.aio.models.generate_content.call_args_list[0].kwargs["model"] == "gemini-3.6-flash"
    assert mock_instance.aio.models.generate_content.call_args_list[1].kwargs["model"] == "gemini-3.5-flash-lite"
    mock_log_usage.assert_awaited_once()
    assert mock_log_usage.call_args.kwargs["model"] == "gemini-3.5-flash-lite"
    assert mock_log_usage.call_args.kwargs["input_tokens"] == 120
    assert mock_log_usage.call_args.kwargs["output_tokens"] == 45

    # Now test complete LLM outage fallback on EN track
    mock_get_cred.side_effect = ["key-primary", "key-primary"]
    mock_instance.aio.models.generate_content = AsyncMock(side_effect=Exception("All models down"))
    en_fallback = await ReportEnrichmentService._generate_script_with_llm(
        "DAILY_VOICE_BRIEF_EN", "Prompt instruction", "中文原始內容不應出現在英文主播保底"
    )
    assert "Good morning. This is your Archon Executive Intelligence Briefing." in en_fallback
    assert "中文" not in en_fallback






