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


async def run_auto_fetch_leads():
    """Clockwork task to trigger Alice's daily lead auto-fetch."""
    logger.info("📡 Clockwork: Triggering daily Alice job search...")
    try:
        from src.server.services.job_board_service import JobBoardService

        service = JobBoardService()
        new_leads = await service.auto_fetch_daily_leads()

        get_supabase_client().table("archon_logs").insert(
            {
                "source": "clockwork-scheduler",
                "level": "INFO",
                "message": f"Daily auto-fetch completed. {new_leads} new leads saved.",
                "details": {"new_leads_count": new_leads},
            }
        ).execute()
        logger.info(f"✅ Clockwork: Alice daily auto-fetch finished ({new_leads} leads).")
    except Exception as e:
        logger.error(f"💥 Clockwork: Alice auto-fetch failed: {e}")


async def run_prune_stale_leads():
    """Clockwork task to prune stale leads (Scenario D Pruning Loop)."""
    logger.info("🧹 Clockwork: Triggering hourly prune stale leads...")
    try:
        from src.server.services.enrichment_service import EnrichmentService

        pruned_count = await EnrichmentService.prune_stale_leads()

        if pruned_count > 0:
            get_supabase_client().table("archon_logs").insert(
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": f"Stale leads pruning completed. {pruned_count} leads archived.",
                    "details": {"pruned_count": pruned_count},
                }
            ).execute()
        logger.info(f"✅ Clockwork: Stale leads pruning finished ({pruned_count} leads archived).")
    except Exception as e:
        logger.error(f"💥 Clockwork: Pruning stale leads failed: {e}")


async def run_daily_market_report():
    """Triggering Bob (MarketingBot) to summarize today's leads."""
    logger.info("✍️ Clockwork: Triggering Bob's Daily Market Report...")
    try:
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service

        supabase = get_supabase_client()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        res = supabase.table("leads").select("company_name, job_title, status").gt("created_at", one_day_ago).execute()
        leads = res.data or []
        if not leads:
            logger.info("✍️ Clockwork: No new leads today to report on. (Cycle logged)")
            return

        cst = ZoneInfo("Asia/Taipei")
        lead_summary = "\n".join([f"- {lead['company_name']} looking for {lead['job_title']}" for lead in leads])
        task_title = f"Daily Market Intelligence ({datetime.now(cst).strftime('%Y-%m-%d')})"
        task_desc = f"""Please write an engaging 600-word daily blog post summarizing today's tech job market movements.

Data points ({len(leads)} leads):
{lead_summary}

Focus on industry trends and written in Traditional Chinese (繁體中文).
Use the tool to save this blog post as a DRAFT."""

        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach marketing task.")
            return

        success, tr = await task_service.create_task(
            project_id=p_res.data[0]["id"], title=task_title, description=task_desc, assignee_id=AgentUUIDs.MARKET_BOT
        )
        if success:
            logger.info(f"✍️ Clockwork: Created Market Report task {tr['task']['id']}. Dispatching Bob...")
            await agent_service.run_agent_task(task_id=tr["task"]["id"], agent_id=AgentUUIDs.MARKET_BOT)
    except Exception as e:
        logger.error(f"💥 Clockwork: Bob market report generation failed: {e}")
