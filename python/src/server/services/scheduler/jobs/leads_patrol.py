"""
Business Monitoring Jobs for Scheduler (Phase 5.9.6 Refactor)
Handles leads, market reports, and sales operations.
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from src.server.config.logfire_config import get_logger
from src.server.services.shared_constants import AgentUUIDs
from src.server.utils import get_supabase_client

logger = get_logger(__name__)


async def run_auto_fetch_leads() -> None:
    """Clockwork task to trigger Alice's daily lead auto-fetch."""
    logger.info("📡 Clockwork: Triggering daily Alice job search...")
    try:
        from src.server.services.job_board_service import JobBoardService

        service = JobBoardService()
        new_leads = await service.auto_fetch_daily_leads()

        from src.server.repositories.base_repository import BaseRepository
        base_repo = BaseRepository(get_supabase_client())
        base_repo.execute_query(
            get_supabase_client().table("archon_logs").insert( # 合法
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": f"Daily auto-fetch completed. {new_leads} new leads saved.",
                    "details": {"new_leads_count": new_leads},
                }
            ),
            "Failed to log auto-fetch completion"
        )
        logger.info(f"✅ Clockwork: Alice daily auto-fetch finished ({new_leads} leads).")
    except Exception as e:
        logger.error(f"💥 Clockwork: Alice auto-fetch failed: {e}")


async def run_prune_stale_leads() -> None:
    """Clockwork task to prune stale leads (Scenario D Pruning Loop)."""
    logger.info("🧹 Clockwork: Triggering hourly prune stale leads...")
    try:
        from src.server.services.enrichment_service import EnrichmentService

        pruned_count = await EnrichmentService.prune_stale_leads()

        if pruned_count > 0:
            from src.server.repositories.base_repository import BaseRepository
            base_repo = BaseRepository(get_supabase_client())
            base_repo.execute_query(
                get_supabase_client().table("archon_logs").insert( # 合法
                    {
                        "source": "clockwork-scheduler",
                        "level": "INFO",
                        "message": f"Stale leads pruning completed. {pruned_count} leads archived.",
                        "details": {"pruned_count": pruned_count},
                    }
                ),
                "Failed to log stale leads pruning"
            )
        logger.info(f"✅ Clockwork: Stale leads pruning finished ({pruned_count} leads archived).")
    except Exception as e:
        logger.error(f"💥 Clockwork: Pruning stale leads failed: {e}")


def generate_lead_outreach_draft(lead: dict) -> str:
    """Generates a personalized, concise 1-on-1 cold outreach message tailored to the lead's pain points."""
    company = lead.get("company_name", "目標企業")
    title = lead.get("job_title", "招募職缺")
    need = (lead.get("identified_need") or "").strip()
    if need and len(need) > 120:
        need = need[:120] + "..."
    elif not need:
        need = "內部系統與業務自動化整合"

    draft = (
        f"🏢 **【{company} - 破冰信模板】**\n"
        f"您好，關注到貴公司正在擴編招募「{title}」，提及「{need}」等關鍵目標。"
        f"我們在 AI 智能代理人工作流與企業跨系統資料串接有成熟的落地案例，能協助縮短 50% 以上的重構與維運負擔。"
        f"若方便，希望能向您或技術主管請益 10 分鐘，交流相關架構實踐經驗。"
    )
    return draft


async def run_market_report() -> bool:
    """Triggering Bob (MarketingBot) to summarize recent leads."""
    logger.info("✍️ Clockwork: Triggering Bob's Market Report...")
    try:
        from src.server.schemas.settings import SchedulerConfig
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.scheduler.utils import get_default_project_id
        from src.server.services.scheduler_service import scheduler_service
        from src.server.services.settings_service import SettingsService

        supabase = get_supabase_client()
        settings = SettingsService(supabase)

        try:
            raw_settings = settings.get_all_settings()
            scheduler_config = SchedulerConfig.model_validate(raw_settings)
        except Exception as e:
            logger.warning(f"LeadsPatrol: Failed to load SchedulerConfig, falling back to defaults. Error: {repr(e)}")
            scheduler_config = SchedulerConfig()

        fallback_td = timedelta(hours=scheduler_config.market_report_fallback_hours)
        # Resolve LAST_RUN_BOB_MARKET_REPORT dynamically via centralized scheduler_service helper
        last_run_dt = await scheduler_service._get_last_run("bob_market_report", supabase=supabase)
        if last_run_dt:
            last_run_time = last_run_dt.isoformat()
        else:
            last_run_time = (datetime.now(UTC) - fallback_td).isoformat()

        from src.server.repositories.base_repository import BaseRepository
        base_repo = BaseRepository(supabase)
        # Qualified Leads Only: Filter for high-intent qualified leads
        success, res_dict = base_repo.execute_query(
            supabase.table("leads")
            .select("company_name, job_title, status, enrichment_score, source_job_url, identified_need")
            .eq("status", "qualified")
            .gt("created_at", last_run_time)
            .order("enrichment_score", desc=True)
            .limit(5),
            "Failed to fetch qualified leads for market report",
        )
        leads = res_dict.get("data", []) if success else []
        if not leads:
            logger.info("✍️ Clockwork: No new qualified leads to report on. (Cycle logged)")
            return False

        cst = ZoneInfo(scheduler_config.system_timezone)
        lead_summary = "\n".join(
            [
                f"- **{lead['company_name']}** (Score: {lead.get('enrichment_score', 0)})\n"
                f"  職缺: {lead['job_title']}\n"
                f"  痛點需求: {lead.get('identified_need', '無詳細需求')[:150]}...\n"
                f"  原始連結: {lead.get('source_job_url', '無')}"
                for lead in leads
            ]
        )
        task_title = f"Daily Market Intelligence ({datetime.now(cst).strftime('%Y-%m-%d')})"

        from src.server.services.prompt_service import prompt_service
        prompt_template = prompt_service.get_prompt("LEADS_PATROL_PROMPT")
        task_desc = prompt_template.format(lead_count=len(leads), lead_summary=lead_summary)

        project_id = get_default_project_id(supabase, "Failed to find project for marketing task")
        if not project_id:
            logger.warning("Clockwork: No projects found to attach marketing task.")
            return False

        success, tr = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AgentUUIDs.MARKET_BOT,
        )
        if success:
            logger.info(f"✍️ Clockwork: Created Market Report task {tr['task']['id']}. Dispatching Bob...")
            await agent_service.run_agent_task(task_id=tr["task"]["id"], agent_id=AgentUUIDs.MARKET_BOT)

            # Generate personalized outreach drafts for Top 1~2 qualified leads
            outreach_drafts = []
            for lead in leads[:2]:
                draft = generate_lead_outreach_draft(lead)
                outreach_drafts.append(draft)
            outreach_section = "\n\n".join(outreach_drafts)

            # Terminal Delivery: Push Qualified Sales Battlecard to Telegram
            try:
                from src.server.services.system.telegram_service import telegram_service

                telegram_report = (
                    f"🎯 **【商業雷達：高意向合格潛客戰鬥簡報】**\n"
                    f"📅 日期：{datetime.now(cst).strftime('%Y-%m-%d %H:%M')}\n"
                    f"📊 本期篩選出 {len(leads)} 家具備高度系統整合痛點之目標企業：\n\n"
                    f"{lead_summary}\n\n"
                    f"✉️ **【客製化痛點破冰信草稿 (一鍵複製)】**\n"
                    f"{outreach_section}\n\n"
                    f"💡 **建議業務行動**：請直接複製上述破冰信草稿聯繫刊登窗口，或透過專業社群進行高精準痛點破冰！"
                )
                await telegram_service.send_message(telegram_report)
                logger.info("✅ Clockwork: Dispatched qualified leads battlecard to Telegram.")
            except Exception as tg_err:
                logger.warning(f"Clockwork: Telegram delivery failed: {tg_err}")

            # Auto-create Sales Follow-up Task in archon_tasks
            try:
                followup_title = f"[Sales Follow-up] Qualified Leads ({datetime.now(cst).strftime('%Y-%m-%d')})"
                followup_desc = (
                    f"## 本期高意向合格潛客名單\n\n{lead_summary}\n\n"
                    f"## 客製化破冰信草稿\n\n{outreach_section}\n\n"
                    f"**行動要求**：請業務團隊於 48 小時內依據上述草稿啟動聯繫並回填進展。"
                )
                f_success, f_res = await task_service.create_task(
                    project_id=project_id,
                    title=followup_title,
                    description=followup_desc,
                    assignee_id=AgentUUIDs.MARKET_BOT,
                )
                if f_success:
                    logger.info("✅ Clockwork: Created Sales Follow-up task in archon_tasks.")
                else:
                    logger.warning(f"Clockwork: Failed to create sales follow-up task: {f_res.get('error')}")
            except Exception as task_err:
                logger.warning(f"Clockwork: Failed to create sales follow-up task: {task_err}")
            return True
        else:
            logger.warning(f"Clockwork: Failed to create market report task: {tr.get('error') if isinstance(tr, dict) else tr}")
            return False
    except Exception as e:
        logger.error(f"💥 Clockwork: Bob market report generation failed: {e}", exc_info=True)
        return False


async def check_and_resume_dag(scheduler) -> None:
    """L2 模組化：檢查今日 leads 相關 DAG 的執行狀態，若遇當機則接力執行未完成的後游任務。"""
    from src.server.schemas.settings import SchedulerConfig
    from src.server.services.settings_service import SettingsService

    settings = SettingsService()
    try:
        raw_settings = settings.get_all_settings()
        scheduler_config = SchedulerConfig.model_validate(raw_settings)
        tz_str = scheduler_config.system_timezone
    except Exception:
        tz_str = "Asia/Taipei"

    tz = ZoneInfo(tz_str)
    now_date = datetime.now(tz).date()

    alice_dt = await scheduler._get_last_run("alice_auto_fetch")
    bob_dt = await scheduler._get_last_run("bob_market_report")

    alice_date = alice_dt.astimezone(tz).date() if alice_dt else None
    bob_date = bob_dt.astimezone(tz).date() if bob_dt else None

    if alice_date == now_date and bob_date != now_date:
        logger.info("🔗 L2 DAG Catchup: Resuming 'bob_market_report'")
        scheduler._trigger_stateful_daily_event(scheduler._run_market_report, "bob_market_report")
