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
    logger.info("📡 Clockwork: Daily Alice job search...")
    try:
        from server.services.job_board_service import JobBoardService
        service = JobBoardService()
        new_leads = await service.auto_fetch_daily_leads()
        get_supabase_client().table("archon_logs").insert({
            "source": "clockwork-scheduler", "level": "INFO",
            "message": f"Daily auto-fetch completed. {new_leads} new leads saved.",
            "details": {"new_leads_count": new_leads}
        }).execute()
    except Exception as e:
        logger.error(f"💥 Alice auto-fetch failed: {e}")

async def run_daily_market_report():
    """Triggering Bob (MarketingBot) to summarize today's leads."""
    logger.info("✍️ Clockwork: Bob's Market Report...")
    try:
        from server.services.agent_service import agent_service
        from server.services.projects.task_service import task_service
        supabase = get_supabase_client()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        res = supabase.table("leads").select("company_name, job_title").gt("created_at", one_day_ago).execute()
        leads = res.data or []
        if not leads:
            return

        lead_summary = "\n".join([f"- {lead['company_name']} looking for {lead['job_title']}" for lead in leads])
        task_title = f"Daily Market Intelligence ({datetime.now().strftime('%Y-%m-%d')})"
        task_desc = f"""Please write an engaging 600-word daily blog post summarizing today's tech job market movements.

Data points ({len(leads)} leads):
{lead_summary}

Focus on industry trends and written in Traditional Chinese (繁體中文).
Use the tool to save this blog post as a DRAFT."""

        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if p_res.data:
            success, tr = await task_service.create_task(project_id=p_res.data[0]["id"], title=task_title, description=task_desc, assignee_id="ai-market-bot")
            if success:
                await agent_service.run_agent_task(task_id=tr['task']['id'], agent_id="ai-market-bot")
    except Exception as e:
        logger.error(f"💥 Bob market report failed: {e}")

async def analyze_token_usage():
    """Token Usage Analysis & Retention."""
    logger.info("🤖 Clockwork: Starting Token Usage Analysis...")
    try:
        supabase = get_supabase_client()
        one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()
        res = supabase.table("gemini_logs").select("user_name, gemini_response").gt("created_at", one_day_ago).execute()
        data = res.data or []

        usage_map: dict[str, int] = {}
        total_tokens = 0
        for entry in data:
            user = entry.get("user_name", "Unknown")
            content = entry.get("gemini_response", "")
            if not content:
                continue
            est = len(content) // 4
            usage_map[user] = usage_map.get(user, 0) + est
            total_tokens += est

        supabase.table("archon_logs").insert({
            "source": "clockwork-scheduler", "level": "INFO",
            "message": f"Daily Token Analysis: {total_tokens} tokens",
            "details": {
                "type": "token_analysis",
                "period": "24h",
                "total_estimated": total_tokens,
                "usage_breakdown": usage_map
            }
        }).execute()
    except Exception as e:
        logger.error(f"💥 Token Analysis Failed: {e}")

async def run_business_sentinel():
    """Scans leads for staleness (Sentinel logic with anti-spam)."""
    logger.info("🛡️ Clockwork: Starting Business Sentinel...")
    try:
        supabase = get_supabase_client()
        threshold = 14
        r_set = supabase.table("archon_settings").select("value").eq("key", "STALE_LEAD_THRESHOLD_DAYS").execute()
        if r_set.data:
            threshold = int(r_set.data[0]["value"])

        cutoff = (datetime.now(UTC) - timedelta(days=threshold)).isoformat()
        seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()

        # 1. Stale Leads
        res = supabase.table("leads").select("id, company_name, updated_at").lt("updated_at", cutoff).not_.in_("status", ["won", "converted"]).limit(20).execute()
        for lead in (res.data or []):
            # Anti-spam
            existing = supabase.table("archon_logs").select("id").eq("source", "sentinel").eq("level", "ALERT").gt("created_at", seven_days_ago).filter("details->>lead_id", "eq", str(lead["id"])).execute()
            if existing.data:
                continue

            supabase.table("archon_logs").insert({
                "source": "sentinel", "level": "ALERT", "message": f"Stale Lead: {lead['company_name']}",
                "details": {"type": "stale_lead", "category": "business", "lead_id": lead["id"], "company": lead["company_name"]}
            }).execute()

        # 2. Content Bottlenecks (GAP-029)
        forty_eight_hours_ago = (datetime.now(UTC) - timedelta(hours=48)).isoformat()
        post_res = supabase.table("blog_posts").select("id, title, updated_at").eq("status", "review").lt("updated_at", forty_eight_hours_ago).execute()
        for post in (post_res.data or []):
            # Anti-spam
            existing_p = supabase.table("archon_logs").select("id").eq("source", "sentinel").eq("level", "ALERT").gt("created_at", seven_days_ago).filter("details->>post_id", "eq", str(post["id"])).execute()
            if existing_p.data:
                continue

            supabase.table("archon_logs").insert({
                "source": "sentinel", "level": "ALERT",
                "message": f"Content Bottleneck: '{post['title']}' stuck in review",
                "details": {"type": "content_bottleneck", "category": "business", "post_id": post["id"], "title": post["title"]}
            }).execute()
    except Exception as e:
        logger.error(f"💥 Business Sentinel Failed: {e}")
