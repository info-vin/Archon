"""
Task Dispatcher Job for Scheduler
Handles reclamation of stuck tasks and dispatching of recurring tasks.
"""

from datetime import UTC, datetime, timedelta

from src.server.config.logfire_config import get_logger
from src.server.services.shared_constants import AgentUUIDs
from src.server.utils import get_supabase_client

logger = get_logger(__name__)


async def run_task_dispatcher() -> None:
    """Scans and dispatches recurring tasks. Reclaims zombie tasks."""
    logger.info("📡 Clockwork: Starting Task Dispatcher (Physical Alignment Mode)...")
    try:
        from src.server.repositories.base_repository import BaseRepository
        from src.server.schemas.settings import TaskDispatcherConfig
        from src.server.services.agent_service import agent_service
        from src.server.services.settings_service import SettingsService
        from src.server.services.system.telegram_service import telegram_service

        supabase = get_supabase_client()
        repo = BaseRepository(supabase)
        settings = SettingsService(supabase)

        # 0. Flush Pending Telegram Alerts
        try:
            success, pending_res = repo.execute_query(
                supabase.table("archon_tasks")
                .select("id, description, created_at")
                .eq("title", "[System] Pending Telegram Alert")
                .eq("status", "todo"),
                "Failed to fetch pending telegram tasks"
            )
            if success and pending_res.get("data"):
                pending_tasks = pending_res["data"]
                if pending_tasks:
                    logger.info(f"📡 Clockwork: Found {len(pending_tasks)} pending Telegram alerts. Flushing queue...")
                    for p_task in pending_tasks:
                        t_id = p_task["id"]
                        raw_desc = p_task["description"]
                        created_at_str = p_task.get("created_at")

                        import json
                        try:
                            payload = json.loads(raw_desc)
                            text = payload.get("text", raw_desc)
                            p_mode = payload.get("parse_mode", "Markdown")
                        except Exception:
                            text = raw_desc
                            p_mode = "Markdown"

                        # TTL Dead Letter Queue: Discard tasks older than 24 hours
                        if created_at_str:
                            try:
                                # Ensure timezone aware parsing
                                task_time = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                                if datetime.now(UTC) - task_time > timedelta(hours=24):
                                    repo.execute_query(
                                        supabase.table("archon_tasks").update({"status": "errored"}).eq("id", t_id),
                                        f"Failed to cancel expired telegram task {t_id}"
                                    )
                                    logger.warning(f"🗑️ Clockwork: Telegram alert {t_id} expired (>24h). Discarded.")
                                    continue
                            except Exception as parse_ex:
                                logger.error(f"Failed to parse created_at for task {t_id}: {parse_ex}")

                        is_sent = await telegram_service.send_message(text, parse_mode=p_mode, is_retry=True)
                        if is_sent:
                            repo.execute_query(
                                supabase.table("archon_tasks").update({"status": "done"}).eq("id", t_id),
                                f"Failed to update telegram task {t_id}"
                            )
                            logger.info(f"✅ Clockwork: Sent and cleared pending Telegram alert {t_id}.")
        except Exception as e:
            logger.error(f"💥 TaskDispatcher: Error flushing telegram queue: {e}")

        # 1. Reclaim stuck tasks (Zombie management)
        raw_settings = settings.get_all_settings()
        try:
            config = TaskDispatcherConfig.model_validate(raw_settings)
        except Exception as e:
            logger.warning(f"Failed to parse TaskDispatcherConfig, falling back to defaults: {e}")
            config = TaskDispatcherConfig()

        timeout_mins = config.task_reclaim_timeout
        threshold = (datetime.now(UTC) - timedelta(minutes=timeout_mins)).isoformat()

        success, reclaim_res = repo.execute_query(
            supabase.table("archon_tasks") # 合法
            .update({"status": "todo", "updated_at": datetime.now(UTC).isoformat()})
            .eq("status", "processing")
            .lt("updated_at", threshold),
            "Reclaim zombie tasks"
        )
        reclaim_data = reclaim_res.get("data", []) if success else []
        if reclaim_data:
            logger.warning(
                f"🚨 Task Sentinel: Reclaimed {len(reclaim_data)} stuck tasks (Timeout > {timeout_mins}m)"
            )
            log_payloads = []
            for t in reclaim_data:
                log_payloads.append(
                    {
                        "source": "task-sentinel",
                        "level": "WARNING",
                        "message": f"Auto-reclaimed stuck task: {t['title']}",
                        "details": {"task_id": t["id"], "type": "timeout_reclamation"},
                    }
                )
            if log_payloads:
                repo.execute_query(supabase.table("archon_logs").insert(log_payloads), "Log task reclamation") # 合法

            # Send Telegram Alert
            alert_threshold = config.zombie_task_alert_threshold
            if len(reclaim_data) > alert_threshold:
                alert_msg = f"🚨 *[Archon Alert] Zombie Task Detected*\nReclaimed {len(reclaim_data)} stuck tasks (Timeout > {timeout_mins}m).\n\n"
                for t in reclaim_data:
                    alert_msg += f"- `{t['title']}`\n"
                await telegram_service.send_message(alert_msg)

        # 2. Dispatch recurring tasks
        success, res = repo.execute_query(
            supabase.table("archon_tasks") # 合法
            .select("id, title, assignee_id, crawler_target_id")
            .eq("is_recurring", True)
            .eq("status", "todo"),
            "Fetch recurring tasks"
        )
        tasks = res.get("data", []) if success else []
        if not tasks:
            logger.info("📡 Clockwork: No pending recurring tasks found.")
            return

        logger.info(f"📡 Clockwork: Found {len(tasks)} tasks ready for automated execution.")
        log_payloads = []
        for task in tasks:
            task_id = task["id"]
            logger.info(f"📡 Clockwork: Dispatching task '{task['title']}' (ID: {task_id})")
            await agent_service.run_agent_task(task_id=task_id, agent_id=task.get("assignee_id", AgentUUIDs.LIBRARIAN))

            # Record in Audit Log
            log_payloads.append(
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
            )
        if log_payloads:
            repo.execute_query(supabase.table("archon_logs").insert(log_payloads), "Log task dispatch") # 合法
    except Exception as e:
        logger.error(f"💥 Clockwork: Task Dispatcher Failed: {e}")
