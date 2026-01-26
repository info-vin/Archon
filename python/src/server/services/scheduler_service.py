import os
import sys
from datetime import datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config.logfire_config import get_logger

logger = get_logger(__name__)

# Logic to find 'scripts' folder which is at Archon/scripts
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
scripts_path = os.path.join(project_root, "scripts")

if scripts_path not in sys.path:
    sys.path.append(scripts_path)

try:
    from probe_librarian import run_probe_logic
except ImportError:
    try:
        from scripts.probe_librarian import run_probe_logic
    except ImportError:
        logger.error(f"❌ scheduler_service: Could not import probe_librarian from {scripts_path}")
        async def run_probe_logic():
            logger.error("❌ Probe logic not found")
            return False

class SchedulerService:
    _instance = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._scheduler = AsyncIOScheduler()
        return cls._instance

    def start(self):
        if not self._scheduler.running:
            logger.info("🕒 Clockwork: Starting Scheduler Service...")
            self._scheduler.start()
            self._schedule_jobs()
        else:
            logger.warning("Clockwork: Scheduler already running.")

    def shutdown(self):
        if self._scheduler.running:
            logger.info("🛑 Clockwork: Shutting down Scheduler...")
            self._scheduler.shutdown()

    def _schedule_jobs(self):
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

    async def _analyze_token_usage(self):
        logger.info("🤖 Clockwork: Starting Token Usage Analysis...")
        try:
            from ..utils import get_supabase_client
            supabase = get_supabase_client()

            one_day_ago = (datetime.utcnow() - timedelta(hours=24)).isoformat()

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
        logger.info("🤖 Clockwork: Triggering System Probe...")
        try:
            from ..utils import get_supabase_client
            supabase = get_supabase_client()

            success = await run_probe_logic()

            log_level = "INFO" if success else "ERROR"
            msg = "System Probe Passed" if success else "System Probe FAILED"
            details = {"type": "probe_librarian", "success": success}

            if success:
                logger.info(f"✅ Clockwork: {msg}")
            else:
                logger.error(f"❌ Clockwork: {msg}")

            try:
                supabase.table("archon_logs").insert({
                    "source": "clockwork-scheduler",
                    "level": log_level,
                    "message": msg,
                    "details": details
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
