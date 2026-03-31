"""
Task Dispatcher Job for Scheduler
Handles reclamation of stuck tasks and dispatching of recurring tasks.
"""

from datetime import UTC, datetime, timedelta

from server.config.logfire_config import get_logger
from server.utils import get_supabase_client

logger = get_logger(__name__)


async def run_task_dispatcher():
    """Scans and dispatches recurring tasks. Reclaims zombie tasks."""
    logger.info("📡 Clockwork: Starting Task Dispatcher (Physical Alignment Mode)...")
    try:
        from server.services.agent_service import agent_service
        from server.services.credential_service import credential_service

        supabase = get_supabase_client()

        # 1. Reclaim stuck tasks (Zombie management)
        timeout_mins = int(await credential_service.get_credential("TASK_RECLAIM_TIMEOUT", 60))
        threshold = (datetime.now(UTC) - timedelta(minutes=timeout_mins)).isoformat()

        reclaim_res = (
            supabase.table("archon_tasks")
            .update({"status": "todo", "updated_at": datetime.now(UTC).isoformat()})
            .eq("status", "processing")
            .lt("updated_at", threshold)
            .execute()
        )
        if reclaim_res.data:
            logger.warning(
                f"🚨 Task Sentinel: Reclaimed {len(reclaim_res.data)} stuck tasks (Timeout > {timeout_mins}m)"
            )
            for t in reclaim_res.data:
                supabase.table("archon_logs").insert(
                    {
                        "source": "task-sentinel",
                        "level": "WARNING",
                        "message": f"Auto-reclaimed stuck task: {t['title']}",
                        "details": {"task_id": t["id"], "type": "timeout_reclamation"},
                    }
                ).execute()

        # 2. Dispatch recurring tasks
        res = (
            supabase.table("archon_tasks")
            .select("id, title, assignee_id, crawler_target_id")
            .eq("is_recurring", True)
            .eq("status", "todo")
            .execute()
        )
        tasks = res.data or []
        if not tasks:
            logger.info("📡 Clockwork: No pending recurring tasks found.")
            return

        logger.info(f"📡 Clockwork: Found {len(tasks)} tasks ready for automated execution.")
        for task in tasks:
            task_id = task["id"]
            logger.info(f"📡 Clockwork: Dispatching task '{task['title']}' (ID: {task_id})")
            await agent_service.run_agent_task(task_id=task_id, agent_id=task.get("assignee_id", "ai-librarian"))

            # Record in Audit Log
            supabase.table("archon_logs").insert(
                {
                    "source": "clockwork-scheduler",
                    "level": "INFO",
                    "message": f"Auto-dispatched recurring task: {task['title']}",
                    "details": {
                        "task_id": task_id,
                        "assignee": task.get("assignee_id"),
                        "target_id": task.get("crawler_target_id"),
                    },
                }
            ).execute()
    except Exception as e:
        logger.error(f"💥 Clockwork: Task Dispatcher Failed: {e}")
