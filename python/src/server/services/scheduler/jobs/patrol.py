"""
Patrol Jobs for Scheduler
Handles system health, log monitoring, and cleanup.
"""

from datetime import UTC, datetime, timedelta

from server.config.logfire_config import get_logger
from server.services.shared_constants import AgentUUIDs

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
            .eq("created_by", AgentUUIDs.LIBRARIAN)
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

async def run_model_verification():
    """Verifies that the system is using the safe Lite model to prevent 429 errors."""
    logger.info("🤖 Clockwork: Running Model Verification...")
    try:
        from server.config.model_ssot import SYSTEM_MODELS
        from server.utils import get_supabase_client

        supabase = get_supabase_client()

        default_pro = SYSTEM_MODELS.get("DEFAULT_PRO", "")
        default_text = SYSTEM_MODELS.get("DEFAULT_TEXT", "")

        # Check if the models are set to lite versions to bypass 20 RPD limit
        is_safe = "lite" in default_pro and "lite" in default_text
        msg = "Model Verification Passed (Using Lite models)" if is_safe else "Model Verification WARNING: Potentially using high-quota models"
        log_level = "INFO" if is_safe else "WARNING"

        logger.info(f"{'✅' if is_safe else '⚠️'} Clockwork: {msg}")

        try:
            supabase.table("archon_logs").insert(
                {"source": "clockwork-scheduler", "level": log_level, "message": msg, "details": {"DEFAULT_PRO": default_pro, "DEFAULT_TEXT": default_text}}
            ).execute()
        except Exception as db_err:
            logger.error(f"❌ Clockwork: Failed to write to archon_logs: {db_err}")

    except Exception as e:
        logger.error(f"💥 Clockwork: Model Verification Crashed: {e}")

async def run_tech_debt_audit():
    """Scans PRPs and scripts for technical debt, and dispatches DevBot if needed."""
    logger.info("🧹 Clockwork: Starting Tech Debt Patrol...")
    try:
        import glob
        import os
        import time

        from server.services.agent_service import agent_service
        from server.services.projects.task_service import task_service
        from server.services.shared_constants import AI_AGENT_ROLES
        from server.utils import get_supabase_client

        warnings = []

        # 1. Check unarchived PRPs
        prp_files = glob.glob("/app/PRPs/Phase_*.md")
        if len(prp_files) >= 5:
            warnings.append(f"PRPs directory is cluttered ({len(prp_files)} unarchived files). Please archive completed phases.")

        # 2. Check stale scripts (older than 14 days)
        fourteen_days_ago = time.time() - (14 * 24 * 3600)
        stale_scripts = []

        script_patterns = ["/app/scripts/*.py", "/app/scripts/*.sh", "/app/python/scripts/*.py"]
        for pattern in script_patterns:
            for filepath in glob.glob(pattern):
                if os.path.isfile(filepath):
                    mtime = os.path.getmtime(filepath)
                    if mtime < fourteen_days_ago:
                        stale_scripts.append(os.path.relpath(filepath, "/app"))

        if stale_scripts:
            stale_msg = f"Found {len(stale_scripts)} stale script(s) (no modifications in > 14 days):\n"
            stale_msg += "\n".join([f"- {s}" for s in stale_scripts[:5]])
            if len(stale_scripts) > 5:
                stale_msg += "\n..."
            warnings.append(stale_msg)

        if not warnings:
            logger.info("✅ Clockwork: Tech Debt Patrol found no issues.")
            return

        logger.info("⚠️ Clockwork: Detected Tech Debt. Creating task for DevBot...")

        task_title = f"Auto-Cleanup: Technical Debt Audit ({datetime.now(UTC).strftime('%Y-%m-%d')})"
        task_desc = "Clockwork detected the following technical debt that needs archiving or cleanup:\n\n" + "\n\n".join(warnings) + "\n\nPlease review and clean up the workspace."

        supabase = get_supabase_client()
        p_res = supabase.table("archon_projects").select("id").limit(1).execute()
        if not p_res.data:
            logger.warning("Clockwork: No projects found to attach tech debt task.")
            return

        project_id = p_res.data[0]["id"]

        success, task_result = await task_service.create_task(
            project_id=project_id,
            title=task_title,
            description=task_desc,
            assignee_id=AI_AGENT_ROLES.get("DevBot (Engineering)") or "ai-dev-bot",
        )

        if success:
            logger.info(f"🧹 Clockwork: Created tech debt task {task_result['task']['id']}. Dispatching DevBot...")
            await agent_service.run_agent_task(
                task_id=task_result["task"]["id"], agent_id=task_result["task"]["assignee_id"]
            )

    except Exception as e:
        logger.error(f"💥 Clockwork: Tech Debt Patrol Failed: {e}")
