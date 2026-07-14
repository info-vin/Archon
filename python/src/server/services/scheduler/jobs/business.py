"""
Business Monitoring Jobs for Scheduler
Handles leads, market reports, and token analysis.
"""

from datetime import UTC, datetime, timedelta

from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import BudgetConfig
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

        lead_summary = "\n".join([f"- {lead['company_name']} looking for {lead['job_title']}" for lead in leads])
        task_title = f"Daily Market Intelligence ({datetime.now().strftime('%Y-%m-%d')})"
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


async def run_daily_executive_summary():
    """Clockwork task to trigger Star-topology Group Chat for Daily Executive Summary."""
    from src.server.services.report_service import report_service

    await report_service.generate_daily_executive_summary()


async def run_weekly_executive_summary():
    """Clockwork task to trigger Map-Reduce for Weekly Executive Summary."""
    from src.server.services.report_service import report_service

    await report_service.generate_weekly_executive_summary()


async def run_monthly_executive_summary():
    """Clockwork task to trigger Map-Reduce for Monthly Executive Summary."""
    from src.server.services.report_service import report_service

    await report_service.generate_monthly_executive_summary()


async def analyze_token_usage():
    """Token Usage Analysis & Proactive Alerting (Phase 6.1: Cost Sentinel)"""
    logger.info("🤖 Clockwork: Starting Token Usage Analysis & Cost Sentinel...")
    try:
        from src.server.services.system.telegram_service import telegram_service
        supabase = get_supabase_client()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        # 1. Daily Analysis
        res_daily = (
            supabase.table("token_usage")
            .select("input_tokens, output_tokens, cost_usd")
            .gt("created_at", one_day_ago)
            .execute()
        )
        data_daily = res_daily.data or []
        total_tokens = sum((row.get("input_tokens", 0) + row.get("output_tokens", 0)) for row in data_daily)
        total_cost = sum(float(row.get("cost_usd", 0)) for row in data_daily)
        logger.info(f"📊 Daily Token Analysis: {total_tokens} physical tokens, ${total_cost:.4f} USD.")

        # 2. Phase 6.1 Cost Sentinel (7-day check)
        res_weekly = (
            supabase.table("token_usage")
            .select("cost_usd")
            .gt("created_at", seven_days_ago)
            .execute()
        )
        data_weekly = res_weekly.data or []
        weekly_cost = sum(float(row.get("cost_usd", 0)) for row in data_weekly)

        from src.server.services.settings_service import SettingsService
        settings = SettingsService(supabase)
        raw_settings = settings.get_all_settings()
        try:
            config = BudgetConfig.model_validate(raw_settings)
        except Exception as e:
            logger.warning(f"Failed to parse BudgetConfig, falling back to defaults: {e}")
            config = BudgetConfig()

        cost_threshold = config.weekly_budget_threshold

        if weekly_cost > cost_threshold:
            msg = f"[CRITICAL] Weekly Budget Exceeded: ${weekly_cost:.4f} USD (Threshold: ${cost_threshold:.2f} USD)"
            logger.error(f"💰 Sentinel: {msg}")
            await telegram_service.send_message(msg)

            supabase.table("archon_logs").insert(
                {
                    "source": "sentinel-cost",
                    "level": "ALERT",
                    "message": msg,
                    "details": {"weekly_cost": weekly_cost, "threshold": cost_threshold},
                }
            ).execute()

        supabase.table("archon_logs").insert(
            {
                "source": "clockwork-scheduler",
                "level": "INFO",
                "message": f"Daily Token Analysis: {total_tokens} physical tokens",
                "details": {
                    "type": "token_analysis",
                    "period": "24h",
                    "total_tokens": total_tokens,
                    "total_cost": total_cost,
                    "weekly_cost": weekly_cost,
                    "request_count": len(data_daily),
                },
            }
        ).execute()
    except Exception as e:
        logger.error(f"💥 Clockwork: Token Analysis Failed: {e}")


async def run_business_sentinel():
    """Scans leads for staleness with Proactive State Intervention (Restored Phase 4.6.46)."""
    logger.info("🛡️ Clockwork: Starting Business Sentinel...")
    try:
        supabase = get_supabase_client()
        threshold_days = 14
        # Physical Fix: Column name is 'key', not 'setting_key'
        res_settings = (
            supabase.table("archon_settings").select("value").eq("key", "STALE_LEAD_THRESHOLD_DAYS").execute()
        )
        if res_settings.data:
            threshold_days = int(res_settings.data[0]["value"])

        cutoff_date = (datetime.now(UTC) - timedelta(days=threshold_days)).isoformat()
        logger.info(f"🛡️ Sentinel: Scanning for leads updated before {cutoff_date} (threshold={threshold_days}d)")

        seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        # 1. Stale Leads with Proactive Intervention
        res = (
            supabase.table("leads")
            .select("id, company_name, updated_at")
            .lt("updated_at", cutoff_date)
            .not_.in_("status", ["won", "converted", "dormant"])
            .limit(20)
            .execute()
        )
        stale_leads = res.data or []
        if not stale_leads:
            logger.info("🛡️ Clockwork: No stale leads found.")
        else:
            log_payloads = []
            for lead in stale_leads:
                # Proactive Action: Mark as dormant to auto-clean Alice's workbench
                supabase.table("leads").update({"status": "dormant"}).eq("id", lead["id"]).execute()

                # Anti-spam: Check if already alerted
                existing = (
                    supabase.table("archon_logs")
                    .select("id")
                    .eq("source", "sentinel")
                    .eq("level", "ALERT")
                    .gt("created_at", seven_days_ago)
                    .filter("details->>lead_id", "eq", str(lead["id"]))
                    .execute()
                )
                if existing.data:
                    continue

                log_payloads.append(
                    {
                        "source": "sentinel",
                        "level": "ALERT",
                        "message": f"Stale Lead Auto-Dormant: {lead['company_name']}",
                        "details": {
                            "type": "stale_lead",
                            "category": "business",
                            "lead_id": lead["id"],
                            "company": lead["company_name"],
                            "action": "status_changed_to_dormant",
                        },
                    }
                )
                logger.info(f"🛡️ Sentinel: Prepared proactive alert for {lead['company_name']}")

            if log_payloads:
                log_res = supabase.table("archon_logs").insert(log_payloads).execute()
                if log_res.data:
                    try:
                        import asyncio

                        from src.server.services.projects.task_service import task_service

                        for log_record in log_res.data:
                            log_id = log_record["id"]
                            asyncio.create_task(
                                task_service.generate_task_from_alert(alert_id=str(log_id), assignee_id=None)
                            )
                    except Exception as task_err:
                        logger.error(f"🛡️ Sentinel: Failed to auto-generate tasks from alerts: {task_err}")

        # 2. Content Bottlenecks (GAP-029)
        forty_eight_hours_ago = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
        post_res = (
            supabase.table("blog_posts")
            .select("id, title, updated_at")
            .eq("status", "review")
            .lt("updated_at", forty_eight_hours_ago)
            .execute()
        )
        posts = post_res.data or []
        log_payloads = []
        for post in posts:
            # Anti-spam
            existing_p = (
                supabase.table("archon_logs")
                .select("id")
                .eq("source", "sentinel")
                .eq("level", "ALERT")
                .gt("created_at", seven_days_ago)
                .filter("details->>post_id", "eq", str(post["id"]))
                .execute()
            )
            if existing_p.data:
                continue

            log_payloads.append(
                {
                    "source": "sentinel",
                    "level": "ALERT",
                    "message": f"Content Bottleneck: '{post['title']}' stuck in review",
                    "details": {
                        "type": "content_bottleneck",
                        "category": "business",
                        "post_id": post["id"],
                        "title": post["title"],
                    },
                }
            )
            logger.info(f"🛡️ Sentinel: Prepared bottleneck alert for {post['title']}")

        if log_payloads:
            supabase.table("archon_logs").insert(log_payloads).execute()
    except Exception as e:
        logger.error(f"💥 Clockwork: Business Sentinel Failed: {e}", exc_info=True)


async def run_api_deprecation_scan():
    """Bi-weekly scan of Google's Gemini API Docs to check for deprecations and limit changes."""
    logger.info("🔍 Clockwork: Starting API Deprecation & Limit Scan...")
    try:
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.shared_constants import AI_AGENT_ROLES

        supabase = get_supabase_client()

        task_title = f"Auto-Scan: Gemini API Deprecations & Quotas ({datetime.now(UTC).strftime('%Y-%m-%d')})"
        task_desc = (
            "Clockwork has initiated the bi-weekly scan of Google's Gemini API documentation.\n\n"
            "Please use your RAG and Web capabilities to extract the latest information regarding:\n"
            "1. Model Deprecations (e.g., gemini-3.1-flash-lite, gemini-3-flash-preview).\n"
            "2. Free Tier API Rate Limits (RPD, RPM) for the Gemini 3/3.1 series.\n\n"
            "Provide a summary of any changes that might affect our system stability."
        )

        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach API scan task.")
            return

        project_id = p_res.data[0]["id"]

        success, task_result = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AI_AGENT_ROLES.get("Librarian (Knowledge)") or AgentUUIDs.LIBRARIAN,
        )

        if success:
            logger.info(f"🔍 Clockwork: Created API scan task {task_result['task']['id']}. Dispatching Librarian...")
            await agent_service.run_agent_task(
                task_id=task_result["task"]["id"], agent_id=task_result["task"]["assignee_id"]
            )

            supabase.table("archon_logs").insert(
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": "Dispatched Bi-Weekly API Limit & Deprecation Scan to Librarian",
                }
            ).execute()

    except Exception as e:
        logger.error(f"💥 Clockwork: API Scan Failed: {e}", exc_info=True)
