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
        from src.server.repositories.base_repository import BaseRepository
        repo = BaseRepository(supabase)
        success_daily, res_daily = repo.execute_query(
            supabase.table("token_usage") # 合法
            .select("input_tokens, output_tokens, cost_usd")
            .gt("created_at", one_day_ago),
            "Fetch daily tokens"
        )
        data_daily = res_daily.get("data", []) if success_daily else []
        total_tokens = sum((row.get("input_tokens", 0) + row.get("output_tokens", 0)) for row in data_daily)
        total_cost = sum(float(row.get("cost_usd", 0)) for row in data_daily)
        logger.info(f"📊 Daily Token Analysis: {total_tokens} physical tokens, ${total_cost:.4f} USD.")

        # 2. Phase 6.1 Cost Sentinel (7-day check)
        success_weekly, res_weekly = repo.execute_query(
            supabase.table("token_usage") # 合法
            .select("cost_usd")
            .gt("created_at", seven_days_ago),
            "Fetch weekly tokens"
        )
        data_weekly = res_weekly.get("data", []) if success_weekly else []
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

            repo.execute_query(
                supabase.table("archon_logs").insert( # 合法
                    {
                        "source": "sentinel-cost",
                        "level": "ALERT",
                        "message": msg,
                        "details": {"weekly_cost": weekly_cost, "threshold": cost_threshold},
                    }
                ),
                "Log budget exceeded"
            )

        total_input = sum(row.get("input_tokens", 0) for row in data_daily)
        total_output = sum(row.get("output_tokens", 0) for row in data_daily)
        total_tokens = total_input + total_output

        repo.execute_query(
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
            ),
            "Log daily analysis"
        )
    except Exception as e:
        logger.error(f"💥 Clockwork: Token Analysis Failed: {e}")


async def run_business_sentinel() -> None:
    """Scans leads for staleness with Proactive State Intervention (Restored Phase 4.6.46)."""
    logger.info("🛡️ Clockwork: Starting Business Sentinel...")
    try:
        supabase = get_supabase_client()
        threshold_days = 14
        from src.server.repositories.base_repository import BaseRepository
        repo = BaseRepository(supabase)
        # Physical Fix: Column name is 'key', not 'setting_key'
        suc_set, res_settings = repo.execute_query(
            supabase.table("archon_settings").select("value").eq("key", "STALE_LEAD_THRESHOLD_DAYS"), # 合法
            "Fetch STALE_LEAD_THRESHOLD_DAYS"
        )
        if suc_set and res_settings.get("data"):
            threshold_days = int(res_settings["data"][0]["value"])

        cutoff_date = (datetime.now(UTC) - timedelta(days=threshold_days)).isoformat()
        logger.info(f"🛡️ Sentinel: Scanning for leads updated before {cutoff_date} (threshold={threshold_days}d)")

        seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        # 1. Stale Leads with Proactive Intervention
        suc_leads, res = repo.execute_query(
            supabase.table("leads") # 合法
            .select("id, company_name, updated_at")
            .lt("updated_at", cutoff_date)
            .not_.in_("status", ["won", "converted", "dormant"]) # 合法
            .limit(20),
            "Fetch stale leads"
        )
        stale_leads = res.get("data", []) if suc_leads else []
        if not stale_leads:
            logger.info("🛡️ Clockwork: No stale leads found.")
        else:
            log_payloads = []
            for lead in stale_leads:
                # Proactive Action: Mark as dormant to auto-clean Alice's workbench
                repo.execute_query(
                    supabase.table("leads").update({"status": "dormant"}).eq("id", lead["id"]), # 合法
                    f"Mark lead {lead['id']} dormant"
                )

                # Anti-spam: Check if already alerted
                suc_ext, existing = repo.execute_query(
                    supabase.table("archon_logs") # 合法
                    .select("id")
                    .eq("source", "sentinel")
                    .eq("level", "ALERT")
                    .gt("created_at", seven_days_ago)
                    .filter("details->>lead_id", "eq", str(lead["id"])),
                    "Check existing alert"
                )
                if suc_ext and existing.get("data"):
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
                suc_log, log_res = repo.execute_query(
                    supabase.table("archon_logs").insert(log_payloads), # 合法
                    "Insert log payloads"
                )
                if suc_log and log_res.get("data"):
                    try:
                        import asyncio

                        from src.server.services.projects.task_service import task_service

                        sem = asyncio.Semaphore(3)

                        async def bounded_generate(alert_id: str):
                            async with sem:
                                await task_service.generate_task_from_alert(alert_id=alert_id, assignee_id=None)

                        await asyncio.gather(*(bounded_generate(str(log_record["id"])) for log_record in log_res["data"]))
                    except Exception as task_err:
                        logger.error(f"🛡️ Sentinel: Failed to auto-generate tasks from alerts: {task_err}")

        # 2. Content Bottlenecks (GAP-029)
        forty_eight_hours_ago = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
        suc_post, post_res = repo.execute_query(
            supabase.table("blog_posts") # 合法
            .select("id, title, updated_at")
            .eq("status", "review")
            .lt("updated_at", forty_eight_hours_ago),
            "Fetch bottleneck posts"
        )
        posts = post_res.get("data", []) if suc_post else []
        log_payloads = []
        for post in posts:
            # Anti-spam
            suc_ext_p, existing_p = repo.execute_query(
                supabase.table("archon_logs") # 合法
                .select("id")
                .eq("source", "sentinel")
                .eq("level", "ALERT")
                .gt("created_at", seven_days_ago)
                .filter("details->>post_id", "eq", str(post["id"])),
                "Check existing post alert"
            )
            if suc_ext_p and existing_p.get("data"):
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
            repo.execute_query(
                supabase.table("archon_logs").insert(log_payloads), # 合法
                "Insert bottleneck logs"
            )
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

        task_desc = prompt_service.get_prompt("API_DEPRECATION_SCAN_PROMPT")

        from src.server.repositories.base_repository import BaseRepository
        repo = BaseRepository(supabase)
        suc_p, p_res = repo.execute_query(
            supabase.table("archon_projects").select("id").limit(1), # 合法
            "Fetch project for API scan"
        )
        if not suc_p or not p_res.get("data"):
            logger.warning("Clockwork: No projects found to attach API scan task.")
            return

        project_id = p_res["data"][0]["id"]

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

            repo.execute_query(
                supabase.table("archon_logs").insert( # 合法
                    {
                        "source": "clockwork-scheduler",
                        "level": "INFO",
                        "message": "Dispatched Bi-Weekly API Limit & Deprecation Scan to Librarian",
                    }
                ),
                "Log API scan dispatch"
            )

    except Exception as e:
        logger.error(f"💥 Clockwork: API Scan Failed: {e}", exc_info=True)
