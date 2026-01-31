from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config.logfire_config import get_logger
from .health_service import HealthService

logger = get_logger(__name__)

class SchedulerService:
    _instance = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._scheduler = AsyncIOScheduler()
        return cls._instance

    def start(self):
        if self._scheduler and not self._scheduler.running:
            logger.info("🕒 Clockwork: Starting Scheduler Service...")
            self._scheduler.start()
            self._schedule_jobs()
        else:
            logger.warning("Clockwork: Scheduler already running or not initialized.")

    def shutdown(self):
        if self._scheduler and self._scheduler.running:
            logger.info("🛑 Clockwork: Shutting down Scheduler...")
            self._scheduler.shutdown()

    def _schedule_jobs(self):
        if not self._scheduler:
            return

        # Job 1: System Heartbeat Probe (Every 6 hours)
        self._scheduler.add_job(
            self._run_system_probe,
            trigger=IntervalTrigger(hours=6),
            id="system_probe",
            replace_existing=True
        )
        logger.info("✅ Scheduled Job: System Probe (Every 6 hours)")

        # Job 2: The Accountant - Token Analysis (Every 24 hours)
        self._scheduler.add_job(
            self._analyze_token_usage,
            trigger=IntervalTrigger(hours=24),
            id="token_analysis",
            replace_existing=True
        )
        logger.info("✅ Scheduled Job: Token Analysis (Every 24 hours)")

        # Job 3: The Patrol - Log Analysis & Auto-Repair (Every 1 hour)
        self._scheduler.add_job(
            self._run_log_patrol,
            trigger=IntervalTrigger(hours=1),
            id="log_patrol",
            replace_existing=True
        )
        logger.info("✅ Scheduled Job: Log Patrol (Every 1 hour)")

    async def _run_log_patrol(self):
        """
        Scans logs for errors and dispatches DevBot if needed.
        """
        logger.info("👮 Clockwork: Starting Log Patrol...")
        try:
            from ..utils import get_supabase_client
            from .agent_service import agent_service
            from .projects.task_service import task_service
            from .shared_constants import AI_AGENT_ROLES

            supabase = get_supabase_client()
            one_hour_ago = (datetime.now(UTC) - timedelta(hours=1)).isoformat()

            # Find recent errors
            res = (
                supabase.table("archon_logs")
                .select("*")
                .eq("level", "ERROR")
                .gt("created_at", one_hour_ago)
                .limit(5) # Avoid spamming tasks
                .execute()
            )

            errors = res.data or []
            if not errors:
                logger.info("👮 Clockwork: No recent errors found. All systems nominal.")
                return

            logger.info(f"👮 Clockwork: Detected {len(errors)} errors. Analyzing...")

            # Simple heuristic: If we find errors, create ONE investigation task
            # In a real system, we would group similar errors.

            # Create a task for DevBot
            error_summary = "\n".join([f"- [{e['source']}] {e['message']}" for e in errors])
            task_title = f"Auto-Repair: System Errors Detected ({datetime.now().strftime('%H:%M')})"
            task_desc = f"Clockwork detected the following errors in the last hour:\n{error_summary}\n\nPlease analyze and fix."

            # We need a project ID to attach the task to.
            # Ideally, there should be a 'System Maintenance' project.
            # For now, we'll try to find one or create it?
            # Or just fail if no project found.
            # Let's assume a default project or pick the first one for MVP.

            p_res = supabase.table("archon_projects").select("id").limit(1).execute()
            if not p_res.data:
                logger.warning("Clockwork: No projects found to attach repair task.")
                return

            project_id = p_res.data[0]["id"]

            # Create Task
            # We explicitly define parameters to ensure type safety and match TaskService.create_task signature
            success, task_result = await task_service.create_task(
                project_id=project_id,
                title=task_title,
                description=task_desc,
                assignee_id=AI_AGENT_ROLES.get("DevBot (Engineering)") or "ai-dev-bot"
            )


            if success:
                logger.info(f"👮 Clockwork: Created repair task {task_result['task']['id']}. Dispatching DevBot...")
                # Dispatch DevBot immediately
                await agent_service.run_agent_task(task_id=task_result['task']['id'], agent_id=task_result['task']["assignee_id"])

        except Exception as e:
            logger.error(f"💥 Clockwork: Log Patrol Failed: {e}")

    async def _analyze_token_usage(self):
        logger.info("🤖 Clockwork: Starting Token Usage Analysis...")
        try:
            from ..utils import get_supabase_client
            supabase = get_supabase_client()

            one_day_ago = (datetime.now(UTC) - timedelta(hours=24)).isoformat()

            # Using parentheses for multi-line chaining (standard Python practice)
            res = (
                supabase.table("gemini_logs")
                .select("user_name, gemini_response")
                .gt("created_at", one_day_ago)
                .execute()
            )

            data = res.data or []
            usage_map = {}
            total_tokens = 0

            for entry in data:
                user = entry.get("user_name", "Unknown")
                content = entry.get("gemini_response", "")
                if not content:
                    continue

                est_tokens = len(content) // 4
                usage_map[user] = usage_map.get(user, 0) + est_tokens
                total_tokens += est_tokens

            logger.info(f"📊 Daily Token Analysis: {total_tokens} tokens estimated across {len(usage_map)} users.")

            details = {
                "type": "token_analysis",
                "period": "24h",
                "usage_breakdown": usage_map,
                "total_estimated": total_tokens
            }

            supabase.table("archon_logs").insert({
                "source": "clockwork-scheduler",
                "level": "INFO",
                "message": f"Daily Token Analysis: {total_tokens} tokens",
                "details": details
            }).execute()

        except Exception as e:
            logger.error(f"💥 Clockwork: Token Analysis Failed: {e}")
            try:
                from ..utils import get_supabase_client
                get_supabase_client().table("archon_logs").insert({
                    "source": "clockwork-scheduler",
                    "level": "ERROR",
                    "message": f"Token Analysis Failed: {str(e)}",
                    "details": {"error": str(e)}
                }).execute()
            except Exception:
                pass

    async def _run_system_probe(self):
        logger.info("🤖 Clockwork: Triggering System Probe via HealthService...")
        try:
            from ..utils import get_supabase_client
            supabase = get_supabase_client()

            # Use the integrated HealthService
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
                supabase.table("archon_logs").insert({
                    "source": "clockwork-scheduler",
                    "level": log_level,
                    "message": msg,
                    "details": result
                }).execute()
            except Exception as db_err:
                logger.error(f"❌ Clockwork: Failed to write to archon_logs: {db_err}")

        except Exception as e:
            logger.error(f"💥 Clockwork: System Probe Crashed: {e}")
            try:
                from ..utils import get_supabase_client
                supabase = get_supabase_client()
                supabase.table("archon_logs").insert({
                    "source": "clockwork-scheduler",
                    "level": "CRITICAL",
                    "message": f"System Probe Crashed: {str(e)}",
                    "details": {"error": str(e)}
                }).execute()
            except Exception:
                pass

scheduler_service = SchedulerService()
