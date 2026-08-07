"""
Sentinel Patrol Jobs for Scheduler (Phase 5.9.6 Refactor)
Handles Token Usage Analysis (Cost Sentinel), Business Bottlenecks, and API limits.
"""

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from src.server.config.logfire_config import get_logger
from src.server.schemas.settings import BudgetConfig
from src.server.services.shared_constants import AgentUUIDs
from src.server.utils import get_supabase_client

logger = get_logger(__name__)


async def analyze_token_usage() -> None:
    """Token Usage Analysis & Proactive Alerting (Phase 6.1: Cost Sentinel)"""
    logger.info("🤖 Clockwork: Starting Token Usage Analysis & Cost Sentinel...")
    try:
        from src.server.services.system.telegram_service import telegram_service
        supabase = get_supabase_client()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        # 1. Daily Analysis
        res_daily = (
            supabase.table("token_usage") # 合法
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
            supabase.table("token_usage") # 合法
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

            supabase.table("archon_logs").insert( # 合法
                {
                    "source": "sentinel-cost",
                    "level": "ALERT",
                    "message": msg,
                    "details": {"weekly_cost": weekly_cost, "threshold": cost_threshold},
                }
            ).execute()

        total_input = sum(row.get("input_tokens", 0) for row in data_daily)
        total_output = sum(row.get("output_tokens", 0) for row in data_daily)
        total_tokens = total_input + total_output

        supabase.table("archon_logs").insert( # 合法
            {
                "source": "clockwork-scheduler",
                "level": "INFO",
                "message": f"Daily Token Analysis: {total_tokens} physical tokens",
                "details": {
                    "type": "token_analysis",
                    "period": "24h",
                    "input_tokens": total_input,
                    "output_tokens": total_output,
                    "total_tokens": total_tokens,
                    "total_cost": total_cost,
                    "weekly_cost": weekly_cost,
                    "request_count": len(data_daily),
                },
            }
        ).execute()
    except Exception as e:
        logger.error(f"💥 Clockwork: Token Analysis Failed: {e}")


async def run_business_sentinel() -> None:
    """Scans leads for staleness with Proactive State Intervention (Restored Phase 4.6.46)."""
    logger.info("🛡️ Clockwork: Starting Business Sentinel...")
    try:
        supabase = get_supabase_client()
        threshold_days = 14
        # Physical Fix: Column name is 'key', not 'setting_key'
        res_settings = (
            supabase.table("archon_settings").select("value").eq("key", "STALE_LEAD_THRESHOLD_DAYS").execute() # 合法
        )
        if res_settings.data:
            threshold_days = int(res_settings.data[0]["value"])

        cutoff_date = (datetime.now(UTC) - timedelta(days=threshold_days)).isoformat()
        logger.info(f"🛡️ Sentinel: Scanning for leads updated before {cutoff_date} (threshold={threshold_days}d)")

        seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        # 1. Stale Leads with Proactive Intervention
        res = (
            supabase.table("leads") # 合法
            .select("id, company_name, updated_at")
            .lt("updated_at", cutoff_date)
            .not_.in_("status", ["won", "converted", "dormant"]) # 合法
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
                supabase.table("leads").update({"status": "dormant"}).eq("id", lead["id"]).execute() # 合法

                # Anti-spam: Check if already alerted
                existing = (
                    supabase.table("archon_logs") # 合法
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
                log_res = supabase.table("archon_logs").insert(log_payloads).execute() # 合法
                if log_res.data:
                    try:
                        import asyncio

                        from src.server.services.projects.task_service import task_service

                        sem = asyncio.Semaphore(3)

                        async def bounded_generate(alert_id: str):
                            async with sem:
                                await task_service.generate_task_from_alert(alert_id=alert_id, assignee_id=None)

                        await asyncio.gather(*(bounded_generate(str(log_record["id"])) for log_record in log_res.data))
                    except Exception as task_err:
                        logger.error(f"🛡️ Sentinel: Failed to auto-generate tasks from alerts: {task_err}")

        # 2. Content Bottlenecks (GAP-029)
        forty_eight_hours_ago = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
        post_res = (
            supabase.table("blog_posts") # 合法
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
                supabase.table("archon_logs") # 合法
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
            supabase.table("archon_logs").insert(log_payloads).execute() # 合法
    except Exception as e:
        logger.error(f"💥 Clockwork: Business Sentinel Failed: {e}", exc_info=True)


async def run_api_deprecation_scan() -> None:
    """Bi-weekly scan of Google's Gemini API Docs to check for deprecations and limit changes."""
    logger.info("🔍 Clockwork: Starting API Deprecation & Limit Scan...")
    try:
        from src.server.services.agent_service import agent_service
        from src.server.services.projects.task_service import task_service
        from src.server.services.prompt_service import prompt_service
        from src.server.services.shared_constants import AI_AGENT_ROLES

        supabase = get_supabase_client()

        cst = ZoneInfo("Asia/Taipei")
        task_title = f"Auto-Scan: Gemini API Deprecations & Quotas ({datetime.now(cst).strftime('%Y-%m-%d')})"

        default_desc = (
            "Clockwork has initiated the bi-weekly scan of Google's Gemini API documentation.\n\n"
            "Please use your RAG and Web capabilities to extract the latest information regarding:\n"
            "1. Model Deprecations (e.g., gemini-3.1-flash-lite, gemini-3-flash-preview).\n"
            "2. Free Tier API Rate Limits (RPD, RPM) for the Gemini 3/3.1 series.\n\n"
            "Provide a summary of any changes that might affect our system stability."
        )
        task_desc = prompt_service.get_prompt("API_DEPRECATION_SCAN_PROMPT", default=default_desc)

        p_res = supabase.table("archon_projects").select("id").limit(1).execute() # 合法
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

            supabase.table("archon_logs").insert( # 合法
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": "Dispatched Bi-Weekly API Limit & Deprecation Scan to Librarian",
                }
            ).execute()

    except Exception as e:
        logger.error(f"💥 Clockwork: API Scan Failed: {e}", exc_info=True)
