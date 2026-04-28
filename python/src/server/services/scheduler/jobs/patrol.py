"""
Patrol Jobs for Scheduler
Handles system health, log monitoring, and cleanup.
"""

from datetime import UTC, datetime, timedelta

from server.config.logfire_config import get_logger

logger = get_logger(__name__)


async def run_system_probe():
    """Triggering System Probe via HealthService."""
    logger.info("🤖 Clockwork: Triggering System Probe via HealthService...")
    try:
        from server.services.health_service import HealthService
        from server.utils import get_supabase_client

        supabase = get_supabase_client()

        health_service = HealthService()
        result = await health_service.check_rag_integrity()

        success = result.get("status") == "healthy"
        log_level = "INFO" if success else "ERROR"
        msg = "System Probe Passed" if success else "System Probe FAILED"

        if success:
            logger.info(f"✅ Clockwork: {msg}")
        else:
            logger.error(f"❌ Clockwork: {msg} | Details: {result.get('details', {}).get('errors')}")

        try:
            supabase.table("archon_logs").insert(
                {"source": "clockwork-scheduler", "level": log_level, "message": msg, "details": result}
            ).execute()
        except Exception as db_err:
            logger.error(f"❌ Clockwork: Failed to write to archon_logs: {db_err}")
    except Exception as e:
        logger.error(f"💥 Clockwork: System Probe Crashed: {e}")
        try:
            from server.utils import get_supabase_client

            get_supabase_client().table("archon_logs").insert(
                {
                    "source": "clockwork-scheduler",
                    "level": "CRITICAL",
                    "message": f"System Probe Crashed: {str(e)}",
                    "details": {"error": str(e)},
                }
            ).execute()
        except Exception:
            pass


async def run_log_patrol():
    """Scans logs for errors and dispatches DevBot."""
    logger.info("👮 Clockwork: Starting Log Patrol...")
    try:
        from server.services.agent_service import agent_service
        from server.services.projects.task_service import task_service
        from server.services.shared_constants import AI_AGENT_ROLES
        from server.utils import get_supabase_client

        supabase = get_supabase_client()
        one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
        res = (
            supabase.table("archon_logs")
            .select("*")
            .eq("level", "ERROR")
            .gt("created_at", one_hour_ago)
            .limit(5)
            .execute()
        )

        errors = res.data or []
        if not errors:
            logger.info("👮 Clockwork: No recent errors found. All systems nominal.")
            return

        logger.info(f"👮 Clockwork: Detected {len(errors)} errors. Analyzing...")
        error_summary = "\n".join([f"- [{e['source']}] {e['message']}" for e in errors])
        task_title = f"Auto-Repair: System Errors Detected ({datetime.now().strftime('%H:%M')})"
        task_desc = (
            f"Clockwork detected the following errors in the last hour:\n{error_summary}\n\nPlease analyze and fix."
        )

        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach repair task.")
            return
        project_id = p_res.data[0]["id"]

        success, task_result = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AI_AGENT_ROLES.get("DevBot (Engineering)") or "ai-dev-bot",
        )

        if success:
            logger.info(f"👮 Clockwork: Created repair task {task_result['task']['id']}. Dispatching DevBot...")

            # Phase 4.6.42: Trigger Cognitive Self-Tuning (Prompt Evolution)
            try:
                from ...system.self_tuning_service import self_tuning_service
                # Pick the first error to tune
                if errors:
                    res = await self_tuning_service.tune_prompt_from_error(str(errors[0]["id"]))
                    if res.get("success"):
                        logger.info(f"🧠 Clockwork: Prompt tuning proposal created: {res.get('proposal_id')}")
            except Exception as tune_err:
                logger.warning(f"🧠 Clockwork: Prompt tuning failed: {tune_err}")

            await agent_service.run_agent_task(
                task_id=task_result["task"]["id"], agent_id=task_result["task"]["assignee_id"]
            )
    except Exception as e:
        logger.error(f"💥 Clockwork: Log Patrol Failed: {e}")


async def cleanup_system_probes():
    """Retention Policy: Deletes Probe data older than 48h."""
    logger.info("🧹 Clockwork: Running System Probe Cleanup...")
    try:
        from server.utils import get_supabase_client

        supabase = get_supabase_client()
        cutoff_time = (datetime.now(UTC) - timedelta(hours=48)).isoformat()

        # 1. Leads cleanup
        res = (
            supabase.table("leads").delete().eq("company_name", "System Probe").lt("created_at", cutoff_time).execute()
        )
        deleted_leads = len(res.data or [])

        # 2. Content pages cleanup
        res_pages = (
            supabase.table("archon_crawled_pages")
            .delete()
            .like("source_id", "pitch-systemprobe-%")
            .lt("created_at", cutoff_time)
            .execute()
        )
        deleted_pages = len(res_pages.data or [])

        # 3. Document versions cleanup
        res_versions = (
            supabase.table("archon_document_versions")
            .delete()
            .eq("created_by", "ai-librarian")
            .like("change_summary", "%System Probe%")
            .lt("created_at", cutoff_time)
            .execute()
        )
        deleted_versions = len(res_versions.data or [])

        # 4. Sources cleanup
        res_sources = (
            supabase.table("archon_sources")
            .delete()
            .like("source_id", "pitch-systemprobe-%")
            .lt("created_at", cutoff_time)
            .execute()
        )
        deleted_sources = len(res_sources.data or [])

        if any([deleted_leads, deleted_pages, deleted_versions, deleted_sources]):
            logger.info(
                f"✅ Clockwork: Cleanup complete. Deleted {deleted_leads} leads, {deleted_pages} pages, {deleted_versions} versions, {deleted_sources} sources."
            )
        else:
            logger.info("✅ Clockwork: Cleanup complete. No expired probe data found.")
    except Exception as e:
        logger.error(f"💥 Clockwork: System Probe Cleanup Failed: {e}")


async def run_business_sentinel():
    """
    Restores Phase 4.6.46 Sentinel: Scans leads for staleness.
    Generates ALERT logs for the Charlie (Manager) Dashboard.
    """
    logger.info("🛡️ Clockwork: Starting Business Sentinel...")
    try:
        from server.utils import get_supabase_client
        supabase = get_supabase_client()

        # 1. Fetch Threshold from settings (Fallback to 14 days)
        threshold_days = 14
        try:
            res_settings = supabase.table("archon_settings").select("value").eq("key", "STALE_LEAD_THRESHOLD_DAYS").execute()
            if res_settings.data:
                threshold_days = int(res_settings.data[0]["value"])
        except Exception:
            pass

        cutoff_date = (datetime.now(UTC) - timedelta(days=threshold_days)).isoformat()
        logger.info(f"🛡️ Sentinel: Scanning for leads updated before {cutoff_date}")

        # 2. Find Stale Leads (NOT won/converted)
        res = (
            supabase.table("leads")
            .select("id, company_name, updated_at, enrichment_score, status")
            .lt("updated_at", cutoff_date)
            .not_.in_("status", ["won", "converted"])
            .limit(20)
            .execute()
        )

        stale_leads = res.data or []
        if not stale_leads:
            logger.info("🛡️ Clockwork: No stale leads found.")
            return

        for lead in stale_leads:
            # Avoid spam: Check if alert exists within last 7 days
            seven_days_ago = (datetime.now(UTC) - timedelta(days=7)).isoformat()
            existing = supabase.table("archon_logs").select("id")\
                .eq("source", "sentinel")\
                .eq("level", "ALERT")\
                .gt("created_at", seven_days_ago)\
                .filter("details->>lead_id", "eq", str(lead["id"]))\
                .execute()

            if not existing.data:
                lead_updated = datetime.fromisoformat(lead["updated_at"].replace('Z', '+00:00'))
                days_stale = (datetime.now(UTC) - lead_updated).days

                alert_payload = {
                    "source": "sentinel",
                    "level": "ALERT",
                    "message": f"Stale Lead Risk: {lead['company_name']} ({days_stale} days inactive)",
                    "details": {
                        "type": "stale_lead",
                        "lead_id": lead["id"],
                        "company": lead["company_name"],
                        "days_stale": days_stale
                    }
                }
                supabase.table("archon_logs").insert(alert_payload).execute()
                logger.info(f"🛡️ Sentinel: Created alert for {lead['company_name']}")

    except Exception as e:
        logger.error(f"💥 Clockwork: Business Sentinel Failed: {e}")
