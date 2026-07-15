"""
Scheduler Service (Phase 5.1.14: Clockwork Optimization)

The central Clockwork engine for Archon.
Implements a consistent Lifecycle & State-Driven architecture:
1. Stateless Patrols (High frequency)
2. Stateful Daily Jobs (Run once per UTC day)
3. Stateful Bi-weekly Maintenance (Run once every 14 days)
"""

from collections.abc import Callable
from datetime import UTC, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.server.config.logfire_config import get_logger
from src.server.services.report_service import report_service
from src.server.services.scheduler.jobs import (
    cleanup_patrol,
    leads_patrol,
    patrol,
    patrol_infra,
    sentinel_patrol,
    task_dispatcher,
    tech_debt_patrol,
)

logger = get_logger(__name__)


def is_hf_awake() -> bool:
    """
    判斷當前時間是否在 HF 的上線視窗內。
    HF Space 睡眠時間為台灣 00:18 ~ 06:41 (CST)。
    """
    # 取得 CST (UTC+8) 時間
    cst_now = datetime.now(UTC).astimezone(timezone(timedelta(hours=8)))
    current_time = cst_now.time()

    sleep_start = time(20, 35)
    sleep_end = time(6, 32)

    if sleep_start <= sleep_end:
        if sleep_start <= current_time <= sleep_end:
            return False
    else:
        # Crosses midnight
        if current_time >= sleep_start or current_time <= sleep_end:
            return False

    return True


class SchedulerService:
    _instance = None
    _scheduler = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._scheduler = AsyncIOScheduler()
        return cls._instance

    async def start(self):
        if self._scheduler and not self._scheduler.running:
            logger.info("🕒 Clockwork: Starting Lifecycle-Driven Scheduler Service...")
            self._scheduler.start()
            await self._schedule_jobs()
        else:
            logger.warning("Clockwork: Scheduler already running.")

    def shutdown(self):
        if self._scheduler and self._scheduler.running:
            logger.info("🛑 Clockwork: Shutting down Scheduler...")
            self._scheduler.shutdown()

    async def _update_last_run(self, job_id: str):
        """Persists the last run timestamp to the database."""
        try:
            from src.server.utils import get_supabase_client

            supabase = get_supabase_client()
            db_key = f"LAST_RUN_{job_id.upper()}"
            now_iso = datetime.now(UTC).isoformat()
            res = supabase.table("archon_settings").select("key").eq("key", db_key).execute()
            if res.data:
                supabase.table("archon_settings").update({"value": now_iso}).eq("key", db_key).execute()
            else:
                supabase.table("archon_settings").insert({"key": db_key, "value": now_iso}).execute()
        except Exception as e:
            logger.error(f"Scheduler: Failed to update last run for {job_id}: {e}")

    async def _get_last_run(self, job_id: str) -> datetime | None:
        """Retrieves the last run timestamp from the database."""
        try:
            from src.server.utils import get_supabase_client

            supabase = get_supabase_client()
            db_key = f"LAST_RUN_{job_id.upper()}"
            res = supabase.table("archon_settings").select("value").eq("key", db_key).execute()
            if res.data:
                return datetime.fromisoformat(res.data[0]["value"].replace("Z", "+00:00"))
        except Exception:
            pass
        return None

    async def _should_run_daily(self, job_id: str) -> bool:
        """Checks if a job has already run today (UTC)."""
        last_run = await self._get_last_run(job_id)
        if not last_run:
            return True
        return last_run.date() < datetime.now(UTC).date()

    async def _should_run_weekly(self, job_id: str) -> bool:
        """Checks if a job has already run in the last 7 days."""
        last_run = await self._get_last_run(job_id)
        if not last_run:
            return True
        return (datetime.now(UTC) - last_run) > timedelta(days=7)

    async def _should_run_monthly(self, job_id: str) -> bool:
        """Checks if a job has already run in the last 30 days."""
        last_run = await self._get_last_run(job_id)
        if not last_run:
            return True
        return (datetime.now(UTC) - last_run) > timedelta(days=30)

    async def _should_run_biweekly(self, job_id: str) -> bool:
        """Checks if a job has already run in the last 14 days."""
        last_run = await self._get_last_run(job_id)
        if not last_run:
            return True
        return (datetime.now(UTC) - last_run) > timedelta(days=14)

    def _schedule_stateless(self, job_func: Callable, job_id: str, delay_mins: int, interval_mins: int):
        """Schedules high-frequency stateless patrols with an initial delay."""
        if not self._scheduler:
            return

        next_run = datetime.now(UTC) + timedelta(minutes=delay_mins)

        # 1. Schedule initial one-time run
        self._scheduler.add_job(job_func, trigger=DateTrigger(run_date=next_run), id=f"{job_id}_initial")

        # 2. Schedule recurring interval
        self._scheduler.add_job(
            job_func,
            trigger=IntervalTrigger(minutes=interval_mins),
            id=job_id,
            replace_existing=True,
            next_run_time=next_run + timedelta(minutes=interval_mins),
        )
        logger.info(f"✅ Scheduled Stateless: {job_id} (Start: +{delay_mins}m, Loop: {interval_mins}m)")

    async def _schedule_stateful_daily(self, job_func: Callable, job_id: str, delay_mins: int, hour: int, minute: int):
        """Schedules a daily job if not already run today, catching up if missed."""
        if not self._scheduler:
            return

        async def wrapper():
            if await self._should_run_daily(job_id):
                logger.info(f"🕒 Clockwork: Executing daily job '{job_id}'")
                try:
                    await job_func()
                finally:
                    await self._update_last_run(job_id)

        run_time = datetime.now(UTC) + timedelta(minutes=delay_mins)
        self._scheduler.add_job(wrapper, trigger=DateTrigger(run_date=run_time), id=f"{job_id}_catchup", replace_existing=True)
        self._scheduler.add_job(
            wrapper,
            trigger=CronTrigger(hour=hour, minute=minute, timezone=ZoneInfo("Asia/Taipei")),
            id=f"{job_id}_recurring",
            replace_existing=True,
        )
        logger.info(f"✅ Scheduled Daily: {job_id} (Catchup: +{delay_mins}m, Cron: {hour:02d}:{minute:02d} CST)")

    async def _schedule_stateful_weekly(self, job_func: Callable, job_id: str, delay_mins: int, day_of_week: str, hour: int, minute: int):
        """Schedules a weekly job, catching up if missed."""
        if not self._scheduler:
            return

        async def wrapper():
            if await self._should_run_weekly(job_id):
                logger.info(f"🕒 Clockwork: Executing weekly job '{job_id}'")
                try:
                    await job_func()
                finally:
                    await self._update_last_run(job_id)

        run_time = datetime.now(UTC) + timedelta(minutes=delay_mins)
        self._scheduler.add_job(wrapper, trigger=DateTrigger(run_date=run_time), id=f"{job_id}_catchup", replace_existing=True)
        self._scheduler.add_job(
            wrapper,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, timezone=ZoneInfo("Asia/Taipei")),
            id=f"{job_id}_recurring",
            replace_existing=True,
        )
        logger.info(f"✅ Scheduled Weekly: {job_id} (Catchup: +{delay_mins}m, Cron: {day_of_week} {hour:02d}:{minute:02d} CST)")

    async def _schedule_stateful_monthly(self, job_func: Callable, job_id: str, delay_mins: int, day: int, hour: int, minute: int):
        """Schedules a monthly job, catching up if missed."""
        if not self._scheduler:
            return

        async def wrapper():
            if await self._should_run_monthly(job_id):
                logger.info(f"🕒 Clockwork: Executing monthly job '{job_id}'")
                try:
                    await job_func()
                finally:
                    await self._update_last_run(job_id)

        run_time = datetime.now(UTC) + timedelta(minutes=delay_mins)
        self._scheduler.add_job(wrapper, trigger=DateTrigger(run_date=run_time), id=f"{job_id}_catchup", replace_existing=True)
        self._scheduler.add_job(
            wrapper,
            trigger=CronTrigger(day=day, hour=hour, minute=minute, timezone=ZoneInfo("Asia/Taipei")),
            id=f"{job_id}_recurring",
            replace_existing=True,
        )
        logger.info(f"✅ Scheduled Monthly: {job_id} (Catchup: +{delay_mins}m, Cron: Day {day} {hour:02d}:{minute:02d} CST)")

    async def _schedule_stateful_biweekly(self, job_func: Callable, job_id: str, delay_mins: int, day_of_week: str, hour: int, minute: int):
        """Schedules a bi-weekly job, catching up if missed."""
        if not self._scheduler:
            return

        async def wrapper():
            if await self._should_run_biweekly(job_id):
                logger.info(f"🕒 Clockwork: Executing bi-weekly maintenance '{job_id}'")
                try:
                    await job_func()
                finally:
                    await self._update_last_run(job_id)

        run_time = datetime.now(UTC) + timedelta(minutes=delay_mins)
        self._scheduler.add_job(wrapper, trigger=DateTrigger(run_date=run_time), id=f"{job_id}_catchup", replace_existing=True)
        self._scheduler.add_job(
            wrapper,
            trigger=CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute, timezone=ZoneInfo("Asia/Taipei")),
            id=f"{job_id}_recurring",
            replace_existing=True,
        )
        logger.info(f"✅ Scheduled Bi-weekly: {job_id} (Catchup: +{delay_mins}m, Cron: {day_of_week} {hour:02d}:{minute:02d} CST)")

    async def _schedule_jobs(self):
        """Phase 5.1.16: Unified Job Lifecycle Strategy including Weekly/Monthly summaries."""
        if not self._scheduler:
            return

        # --- Category 1: Stateless Patrols (1-4 mins) ---
        self._schedule_stateless(self._run_system_probe, "system_probe", 1, 15)
        self._schedule_stateless(self._run_log_patrol, "log_patrol", 2, 30)
        self._schedule_stateless(self._run_task_dispatcher, "task_dispatcher", 3, 30)
        self._schedule_stateless(self._run_model_verification, "model_verification", 4, 120)
        self._schedule_stateless(self._run_meta_twin_audit, "meta_twin_audit", 4, 10)

        # --- Category 2: Stateful Daily Jobs (5-35 mins) ---
        await self._schedule_stateful_daily(self._cleanup_system_probes, "system_probe_cleanup", 5, 7, 20)
        await self._schedule_stateful_daily(self._run_auto_fetch_leads, "alice_auto_fetch", 6, 7, 0)
        await self._schedule_stateful_daily(self._run_daily_market_report, "bob_market_report", 10, 7, 40)
        await self._schedule_stateful_daily(self._run_prune_stale_leads, "prune_stale_leads", 15, 7, 20)
        await self._schedule_stateful_daily(self._analyze_token_usage, "token_analysis", 20, 8, 20)
        await self._schedule_stateful_daily(self._run_business_sentinel, "business_sentinel", 25, 8, 40)
        await self._schedule_stateful_daily(self._run_daily_executive_summary, "daily_executive_summary", 35, 8, 0)

        # --- Category 3: Stateful Weekly / Monthly Jobs (38-42 mins) ---
        await self._schedule_stateful_weekly(self._run_weekly_executive_summary, "weekly_executive_summary", 38, "mon", 9, 0)
        await self._schedule_stateful_monthly(self._run_monthly_executive_summary, "monthly_executive_summary", 42, 1, 9, 0)

        # --- Category 4: Stateful Bi-weekly Maintenance (45-50 mins) ---
        await self._schedule_stateful_biweekly(self._run_infrastructure_audit, "infrastructure_audit", 48, "sat", 7, 10)
        await self._schedule_stateful_biweekly(self._run_api_deprecation_scan, "api_deprecation_scan", 50, "sat", 9, 0)

        self._scheduler.remove_job("tech_debt_audit") if self._scheduler.get_job("tech_debt_audit") else None
        await self._schedule_stateful_biweekly(self._run_tech_debt_audit, "tech_debt_audit", 45, "sun", 9, 0)

    # Delegation Methods
    async def _run_system_probe(self):
        await patrol.run_system_probe()

    async def _run_log_patrol(self):
        await patrol.run_log_patrol()

    async def _cleanup_system_probes(self):
        await cleanup_patrol.cleanup_system_probes()

    async def _run_tech_debt_audit(self):
        await tech_debt_patrol.run_tech_debt_audit()

    async def _run_model_verification(self):
        await patrol.run_model_verification()

    async def _run_infrastructure_audit(self):
        await patrol_infra.run_infrastructure_audit()

    async def _run_prune_stale_leads(self):
        await leads_patrol.run_prune_stale_leads()

    async def _run_auto_fetch_leads(self):
        await leads_patrol.run_auto_fetch_leads()

    async def _analyze_token_usage(self):
        await sentinel_patrol.analyze_token_usage()

    async def _run_business_sentinel(self):
        await sentinel_patrol.run_business_sentinel()

    async def run_business_sentinel(self):
        """Public alias for manual triggering from other services."""
        await sentinel_patrol.run_business_sentinel()

    async def _run_daily_market_report(self):
        await leads_patrol.run_daily_market_report()

    async def _run_daily_executive_summary(self):
        await report_service.generate_daily_executive_summary()

    async def _run_weekly_executive_summary(self):
        await report_service.generate_weekly_executive_summary()

    async def _run_monthly_executive_summary(self):
        await report_service.generate_monthly_executive_summary()

    async def _run_api_deprecation_scan(self):
        await sentinel_patrol.run_api_deprecation_scan()

    async def _run_task_dispatcher(self):
        await task_dispatcher.run_task_dispatcher()

    async def _run_meta_twin_audit(self):
        from .system.meta_twin_service import meta_twin_service
        await meta_twin_service.run_telemetry_audit()


scheduler_service = SchedulerService()
