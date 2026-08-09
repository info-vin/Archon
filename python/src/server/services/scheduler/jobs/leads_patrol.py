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


async def run_daily_market_report() -> None:
    """Triggering Bob (MarketingBot) to summarize today's leads."""
    logger.info("✍️ Clockwork: Triggering Bob's Daily Market Report...")
    try:
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service

        supabase = get_supabase_client()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        from src.server.repositories.base_repository import BaseRepository
        base_repo = BaseRepository(supabase)
        success, res_dict = base_repo.execute_query(
            supabase.table("leads").select("company_name, job_title, status").gt("created_at", one_day_ago),
            "Failed to fetch leads for market report"
        )
        leads = res_dict.get("data", []) if success else []
        if not leads:
            logger.info("✍️ Clockwork: No new leads today to report on. (Cycle logged)")
            return

        cst = ZoneInfo("Asia/Taipei")
        lead_summary = "\n".join([f"- {lead['company_name']} looking for {lead['job_title']}" for lead in leads])
        task_title = f"Daily Market Intelligence ({datetime.now(cst).strftime('%Y-%m-%d')})"

        fallback_str = """Please write an engaging 600-word daily blog post summarizing today's tech job market movements.

Data points ({lead_count} leads):
{lead_summary}

Focus on industry trends and written in Traditional Chinese (繁體中文).
Use the tool to save this blog post as a DRAFT."""

        from src.server.services.prompt_service import prompt_service
        prompt_template = prompt_service.get_prompt("LEADS_PATROL_PROMPT", default=fallback_str)
        task_desc = prompt_template.format(lead_count=len(leads), lead_summary=lead_summary)

        success, p_res_dict = base_repo.execute_query(
            supabase.table("archon_projects").select("id").limit(1),
            "Failed to find project for marketing task"
        )
        if not success or not p_res_dict.get("data"):
            logger.warning("Clockwork: No projects found to attach marketing task.")
            return

        success, tr = await task_service.create_task(
            project_id=p_res_dict["data"][0]["id"], title=task_title, description=task_desc, assignee_id=AgentUUIDs.MARKET_BOT
        )
        if success:
            logger.info(f"✍️ Clockwork: Created Market Report task {tr['task']['id']}. Dispatching Bob...")
            await agent_service.run_agent_task(task_id=tr["task"]["id"], agent_id=AgentUUIDs.MARKET_BOT)
    except Exception as e:
        logger.error(f"💥 Clockwork: Bob market report generation failed: {e}")


async def check_and_resume_dag(scheduler) -> None:
    """L2 模組化：檢查今日 leads 相關 DAG 的執行狀態，若遇當機則接力執行未完成的後游任務。"""
    from src.server.config.config import get_config
    from src.server.services.settings_service import SettingsService

    settings = SettingsService()
    config = get_config()
    env_prefix = config.archon_env or ""
    if env_prefix and not env_prefix.endswith("_"):
        env_prefix += "_"

    def get_last_run_date(job_id: str):
        db_key = f"{env_prefix}LAST_RUN_{job_id.upper()}"
        val = settings.get_setting(db_key)
        if val:
            try:
                return datetime.fromisoformat(val.replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Taipei")).date()
            except Exception:
                pass
        return None

    now_date = datetime.now(ZoneInfo("Asia/Taipei")).date()

    alice_date = get_last_run_date("alice_auto_fetch")
    bob_date = get_last_run_date("bob_market_report")
    exec_date = get_last_run_date("daily_executive_summary")

    if alice_date == now_date and bob_date != now_date:
        logger.info("🔗 L2 DAG Catchup: Resuming 'bob_market_report'")
        scheduler._trigger_stateful_daily_event(scheduler._run_daily_market_report, "bob_market_report")
    elif bob_date == now_date and exec_date != now_date:
        logger.info("🔗 L2 DAG Catchup: Resuming 'daily_executive_summary'")
        scheduler._trigger_stateful_daily_event(scheduler._run_daily_executive_summary, "daily_executive_summary")
