"""
Scheduler Service (Refactored)

The central Clockwork engine for Archon.
Logic is delegated to 'jobs/' sub-modules for modularity.
"""

from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from src.server.config.logfire_config import get_logger
from src.server.services.scheduler.jobs import business, patrol, task_dispatcher

logger = get_logger(__name__)


class SchedulerService:
    _instance = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._scheduler = AsyncIOScheduler()
        return cls._instance

    async def _get_setting(self, key: str, default: int) -> int:
        """Helper to fetch numerical settings from DB with safety bounds."""
        try:
            from src.server.utils import get_supabase_client

            supabase = get_supabase_client()
            res = supabase.table("archon_settings").select("value").eq("key", key).execute()
            if res.data:
                val = int(res.data[0]["value"])
                # Physical Safety Bound: 1 min to 24 hours
                return max(1, min(val, 1440))
        except Exception as e:
            logger.warning(f"Scheduler: Failed to fetch {key}, using default {default}: {e}")
        return default

    async def start(self):
        if self._scheduler and not self._scheduler.running:
            logger.info("🕒 Clockwork: Starting Scheduler Service...")
            self._scheduler.start()
            await self._schedule_jobs()
        else:
            logger.warning("Clockwork: Scheduler already running.")

    def shutdown(self):
        if self._scheduler and self._scheduler.running:
            logger.info("🛑 Clockwork: Shutting down Scheduler...")
            self._scheduler.shutdown()

    async def _update_last_run(self, key: str):
        """Robust last run persistence."""
        try:
            from src.server.utils import get_supabase_client

            supabase = get_supabase_client()
            now_iso = datetime.now(UTC).isoformat()
            res = supabase.table("archon_settings").select("key").eq("key", key).execute()
            if res.data:
                supabase.table("archon_settings").update({"value": now_iso}).eq("key", key).execute()
            else:
                supabase.table("archon_settings").insert({"key": key, "value": now_iso}).execute()
        except Exception as e:
            logger.error(f"Scheduler: Failed to update last run for {key}: {e}")

    async def _get_last_run(self, key: str) -> datetime | None:
        """Robust last run retrieval."""
        try:
            from src.server.utils import get_supabase_client

            supabase = get_supabase_client()
            res = supabase.table("archon_settings").select("value").eq("key", key).execute()
            if res.data:
                return datetime.fromisoformat(res.data[0]["value"].replace("Z", "+00:00"))
        except Exception:
            pass
        return None

    async def _schedule_stateful_job(self, job_func, trigger_hours: int, job_id: str):
        """Schedules a job while ensuring it doesn't skip cycles based on last run in DB."""
        db_key = f"LAST_RUN_{job_id.upper()}"
        last_run = await self._get_last_run(db_key)

        now = datetime.now(UTC)
        # Baseline Restoration: Wait 30s after startup to allow Docker Health Check to pass
        next_run = now + timedelta(seconds=30)
        if last_run:
            expected = last_run + timedelta(hours=trigger_hours)
            if expected > now:
                next_run = expected

        async def stateful_wrapper():
            logger.info(f"🕒 Clockwork: Executing stateful job '{job_id}'")
            try:
                await job_func()
            finally:
                await self._update_last_run(db_key)

        if self._scheduler:
            self._scheduler.add_job(
                stateful_wrapper,
                trigger=IntervalTrigger(hours=trigger_hours),
                id=job_id,
                replace_existing=True,
                next_run_time=next_run,
            )
            logger.info(
                f"✅ Scheduled Job: {job_id} (Every {trigger_hours}h, Next: {next_run.strftime('%Y-%m-%d %H:%M:%S UTC')})"
            )

    async def _schedule_jobs(self):
        if not self._scheduler:
            return

        probe_mins = await self._get_setting("SCHEDULER_PROBE_INTERVAL_MINS", 60)
        patrol_mins = await self._get_setting("SCHEDULER_PATROL_INTERVAL_MINS", 60)
        sentinel_hours = await self._get_setting("SCHEDULER_SENTINEL_INTERVAL_HOURS", 12)

        # 1. Patrol Jobs
        self._scheduler.add_job(
            self._run_system_probe,
            trigger=IntervalTrigger(minutes=probe_mins),
            id="system_probe",
            replace_existing=True,
        )
        logger.info(f"✅ Scheduled Job: System Probe (Every {probe_mins} mins)")

        self._scheduler.add_job(
            self._cleanup_system_probes,
            trigger=IntervalTrigger(hours=1),
            id="system_probe_cleanup",
            replace_existing=True,
        )

        self._scheduler.add_job(
            self._run_log_patrol, trigger=IntervalTrigger(minutes=patrol_mins), id="log_patrol", replace_existing=True
        )
        logger.info(f"✅ Scheduled Job: Log Patrol (Every {patrol_mins} mins)")

        self._scheduler.add_job(
            self._run_model_verification, trigger=IntervalTrigger(minutes=60), id="model_verification", replace_existing=True
        )
        logger.info("✅ Scheduled Job: Model Verification (Every 60 mins)")

        # 2. Business Jobs (Stateful)
        await self._schedule_stateful_job(self._run_prune_stale_leads, 1, "prune_stale_leads")
        await self._schedule_stateful_job(self._run_auto_fetch_leads, 24, "alice_auto_fetch")
        await self._schedule_stateful_job(self._analyze_token_usage, 24, "token_analysis")
        await self._schedule_stateful_job(self._run_business_sentinel, sentinel_hours, "business_sentinel")
        await self._schedule_stateful_job(self._run_daily_market_report, 24, "bob_market_report")
        await self._schedule_stateful_job(self._run_tech_debt_audit, 336, "tech_debt_audit")
        await self._schedule_stateful_job(self._run_api_deprecation_scan, 336, "api_deprecation_scan")

        # 3. Task Dispatcher
        self._scheduler.add_job(
            self._run_task_dispatcher, trigger=IntervalTrigger(minutes=30), id="task_dispatcher", replace_existing=True
        )
        logger.info("✅ Scheduled Job: Task Dispatcher (Every 30 mins)")

    # Delegation Methods
    async def _run_system_probe(self):
        await patrol.run_system_probe()

    async def _run_log_patrol(self):
        await patrol.run_log_patrol()

    async def _cleanup_system_probes(self):
        await patrol.cleanup_system_probes()

    async def _run_tech_debt_audit(self):
        await patrol.run_tech_debt_audit()

    async def _run_model_verification(self):
        await patrol.run_model_verification()

    async def _run_prune_stale_leads(self):
        await business.run_prune_stale_leads()

    async def _run_auto_fetch_leads(self):
        await business.run_auto_fetch_leads()

    async def _analyze_token_usage(self):
        await business.analyze_token_usage()

    async def _run_business_sentinel(self):
        await business.run_business_sentinel()

    async def run_business_sentinel(self):
        await business.run_business_sentinel()

    async def _run_daily_market_report(self):
        await business.run_daily_market_report()

    async def _run_daily_executive_summary(self):
        await business.run_daily_executive_summary()

    async def _run_api_deprecation_scan(self):
        await business.run_api_deprecation_scan()

    async def _run_task_dispatcher(self):
        await task_dispatcher.run_task_dispatcher()


scheduler_service = SchedulerService()
