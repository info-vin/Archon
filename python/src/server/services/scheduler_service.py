import os
import sys

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config.logfire_config import get_logger

logger = get_logger(__name__)

# Logic to find 'scripts' folder which is at Archon/scripts
# this file is at Archon/python/src/server/services/scheduler_service.py
# So we go up 4 levels: services -> server -> src -> python -> Archon
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SCRIPTS_DIR = os.path.join(BASE_DIR, '../scripts') # Wait, BASE_DIR is python/ ? No.
# Let's be safer.
# Current file: .../python/src/server/services/scheduler_service.py
# os.path.dirname(__file__) = services
# .../server
# .../src
# .../python
# .../Archon (Project Root)

# Actually, let's just find the project root relative to this file.
# file: python/src/server/services/scheduler_service.py
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../"))
scripts_path = os.path.join(project_root, "scripts")

if scripts_path not in sys.path:
    sys.path.append(scripts_path)

try:
    from probe_librarian import run_probe_logic
except ImportError:
    # Try importing as package if scripts is in path
    try:
        from scripts.probe_librarian import run_probe_logic
    except ImportError:
        logger.error(f"❌ scheduler_service: Could not import probe_librarian from {scripts_path}")
        # dummy fallback to prevent crash
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

    async def _run_system_probe(self):
        logger.info("🤖 Clockwork: Triggering System Probe...")
        try:
            # Import dependency inside method to avoid circular imports or early init issues
            from ..utils import get_supabase_client
            supabase = get_supabase_client()

            success = await run_probe_logic()

            log_level = "INFO" if success else "ERROR"
            msg = "System Probe Passed" if success else "System Probe FAILED"
            details = {"type": "probe_librarian", "success": success}

            # Log to Console
            if success:
                logger.info(f"✅ Clockwork: {msg}")
            else:
                logger.error(f"❌ Clockwork: {msg}")

            # Log to DB (archon_logs)
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
            # Try to log crash to DB if possible
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
