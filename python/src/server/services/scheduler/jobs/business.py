"""
Business Monitoring Jobs for Scheduler
Handles leads, market reports, and token analysis.
"""

from datetime import UTC, datetime, timedelta

from server.config.logfire_config import get_logger
from server.utils import get_supabase_client

logger = get_logger(__name__)


async def run_auto_fetch_leads():
    """Clockwork task to trigger Alice's daily lead auto-fetch."""
    logger.info("📡 Clockwork: Triggering daily Alice job search...")
    try:
        from server.services.job_board_service import JobBoardService

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


async def run_daily_market_report():
    """Triggering Bob (MarketingBot) to summarize today's leads."""
    logger.info("✍️ Clockwork: Triggering Bob's Daily Market Report...")
    try:
        from server.services.agent_service import agent_service
        from server.services.projects.task_service import task_service

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
            project_id=p_res.data[0]["id"], title=task_title, description=task_desc, assignee_id="ai-market-bot"
        )
        if success:
            logger.info(f"✍️ Clockwork: Created Market Report task {tr['task']['id']}. Dispatching Bob...")
            await agent_service.run_agent_task(task_id=tr["task"]["id"], agent_id="ai-market-bot")
    except Exception as e:
        logger.error(f"💥 Clockwork: Bob market report generation failed: {e}")


async def analyze_token_usage():
    """Token Usage Analysis & Proactive Alerting (Phase 4.6.46: Proactive)"""
    logger.info("🤖 Clockwork: Starting Token Usage Analysis...")
    try:
        supabase = get_supabase_client()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        # Physical Fix: table is token_usage
        res = supabase.table("token_usage").select("input_tokens, output_tokens, cost_usd").gt("created_at", one_day_ago).execute()
        data = res.data or []

        # PERFORMANCE: Replaced two sum() generators with single for loop pass
        total_tokens = 0
        total_cost = 0.0
        for row in data:
            total_tokens += row.get("input_tokens", 0) + row.get("output_tokens", 0)
            total_cost += float(row.get("cost_usd", 0))

        # 1. INFO Log
        logger.info(f"📊 Daily Token Analysis: {total_tokens} physical tokens, ${total_cost:.4f} USD.")

        # 2. PROACTIVE ALERT (Restored Milestone)
        # Alert if cost exceeds threshold (Default $1.0)
        cost_threshold = 1.0
        if total_cost > cost_threshold:
            supabase.table("archon_logs").insert({
                "source": "sentinel-cost",
                "level": "ALERT",
                "message": f"💰 Cost Spike Detected: 24h spend ${total_cost:.2f} > threshold ${cost_threshold:.2f}",
                "details": {"total_cost": total_cost, "total_tokens": total_tokens, "request_count": len(data)}
            }).execute()

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
                    "request_count": len(data),
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
        # Physical Fix: Column name is 'setting_key', not 'key'
        res_settings = (
            supabase.table("archon_settings").select("setting_value").eq("setting_key", "STALE_LEAD_THRESHOLD_DAYS").execute()
        )
        if res_settings.data:
            threshold_days = int(res_settings.data[0]["setting_value"])

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

                alert_payload = {
                    "source": "sentinel",
                    "level": "ALERT",
                    "message": f"Stale Lead Auto-Dormant: {lead['company_name']}",
                    "details": {
                        "type": "stale_lead",
                        "category": "business",
                        "lead_id": lead["id"],
                        "company": lead["company_name"],
                        "action": "status_changed_to_dormant"
                    },
                }
                supabase.table("archon_logs").insert(alert_payload).execute()
                logger.info(f"🛡️ Sentinel: Created proactive alert for {lead['company_name']}")

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

            alert_payload = {
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
            supabase.table("archon_logs").insert(alert_payload).execute()
            logger.info(f"🛡️ Sentinel: Created bottleneck alert for {post['title']}")
    except Exception as e:
        logger.error(f"💥 Clockwork: Business Sentinel Failed: {e}", exc_info=True)
