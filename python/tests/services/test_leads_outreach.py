from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.scheduler.jobs.leads_patrol import generate_lead_outreach_draft, run_market_report


def test_generate_lead_outreach_draft_complete():
    """Verify outreach draft generation with rich lead info."""
    lead = {
        "company_name": "宏達未來科技",
        "job_title": "AI 系統工程師",
        "identified_need": "需要將地端 ERP 與雲端 LLM 進行 API 整合，面臨併發與逾時問題",
    }
    draft = generate_lead_outreach_draft(lead)

    assert "宏達未來科技" in draft
    assert "AI 系統工程師" in draft
    assert "ERP 與雲端 LLM" in draft
    assert "破冰信模板" in draft


def test_generate_lead_outreach_draft_fallback():
    """Verify outreach draft generation with empty fields."""
    lead = {}
    draft = generate_lead_outreach_draft(lead)

    assert "目標企業" in draft
    assert "招募職缺" in draft
    assert "內部系統與業務自動化整合" in draft


@pytest.mark.asyncio
@patch("src.server.services.settings_service.SettingsService.get_all_settings", return_value={})
@patch("src.server.services.settings_service.SettingsService.get_setting", return_value="2026-10-01T00:00:00Z")
@patch("src.server.utils.get_supabase_client")
@patch("src.server.repositories.base_repository.BaseRepository.execute_query")
@patch("src.server.services.projects.task_service.task_service.create_task", new_callable=AsyncMock)
@patch("src.server.services.agent_service.agent_service.run_agent_task", new_callable=AsyncMock)
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
async def test_run_market_report_creates_outreach_and_followup_task(
    mock_tg_send, mock_run_agent, mock_create_task, mock_exec_query, mock_get_supabase, mock_get_setting, mock_get_all_settings
):
    """Verify that run_market_report creates outreach drafts in telegram and a sales follow-up task."""
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    mock_leads = [
        {
            "id": "lead-1",
            "company_name": "聯發創想股份有限公司",
            "job_title": "資深 Python 架構師",
            "identified_need": "多代理人通訊架構設計與非同步爬蟲防護",
            "source_job_url": "https://104.com.tw/job/1",
            "enrichment_score": 90,
        }
    ]

    mock_project = [{"id": "proj-123"}]

    def mock_query_fn(query, message="", *args, **kwargs):
        msg = str(message).lower()
        if "project" in msg:
            return True, {"data": mock_project}
        if "leads" in msg:
            return True, {"data": mock_leads}
        return True, {"data": []}

    mock_exec_query.side_effect = mock_query_fn

    mock_create_task.side_effect = [
        (True, {"task": {"id": "market-task-1"}}),
        (True, {"task": {"id": "followup-task-2"}}),
    ]

    await run_market_report()

    # Verify Market task created
    assert mock_create_task.call_count == 2

    # Verify Telegram message includes outreach draft
    mock_tg_send.assert_awaited_once()
    tg_content = mock_tg_send.call_args[0][0]
    assert "客製化痛點破冰信草稿" in tg_content
    assert "聯發創想股份有限公司" in tg_content

    # Verify Sales follow-up task
    followup_call = mock_create_task.call_args_list[1]
    assert "[Sales Follow-up]" in followup_call[1]["title"]
    assert "聯發創想股份有限公司" in followup_call[1]["description"]
    assert followup_call[1]["assignee_id"] == "a11ce000-0000-0000-0000-000000000000"


@pytest.mark.asyncio
@patch("src.server.services.settings_service.SettingsService.get_all_settings", return_value={})
@patch("src.server.services.settings_service.SettingsService.get_setting", return_value="2026-10-01T00:00:00Z")
@patch("src.server.utils.get_supabase_client")
@patch("src.server.repositories.base_repository.BaseRepository.execute_query")
@patch("src.server.services.projects.task_service.task_service.create_task", new_callable=AsyncMock)
@patch("src.server.services.agent_service.agent_service.run_agent_task", new_callable=AsyncMock)
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
async def test_run_market_report_handles_followup_creation_failure(
    mock_tg_send, mock_run_agent, mock_create_task, mock_exec_query, mock_get_supabase, mock_get_setting, mock_get_all_settings
):
    """Verify that failure to create followup task is safely logged without breaking execution."""
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    mock_leads = [
        {
            "id": "lead-1",
            "company_name": "測試科技",
            "job_title": "AI 工程師",
            "identified_need": "整合測試",
            "source_job_url": "https://example.com",
            "enrichment_score": 85,
        }
    ]

    mock_project = [{"id": "proj-123"}]

    def mock_query_fn(query, message="", *args, **kwargs):
        msg = str(message).lower()
        if "project" in msg:
            return True, {"data": mock_project}
        if "leads" in msg:
            return True, {"data": mock_leads}
        return True, {"data": []}

    mock_exec_query.side_effect = mock_query_fn

    # First task succeeds, followup task returns False
    mock_create_task.side_effect = [
        (True, {"task": {"id": "market-task-1"}}),
        (False, {"error": "Simulated task creation failure"}),
    ]

    # Must complete without unhandled exception
    await run_market_report()
    assert mock_create_task.call_count == 2

