"""
Scheduler Service (Phase 5.9.17: DRY Refactoring & Dynamic Times)

The central Clockwork engine for Archon.
Implements a consistent Lifecycle & State-Driven architecture:
1. Stateless Patrols (High frequency)
2. Stateful Daily Jobs (Run once per UTC day)
3. Stateful Bi-weekly Maintenance (Run once every 14 days)
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from tenacity import retry, stop_after_attempt, wait_chain, wait_fixed

from src.server.config.logfire_config import get_logger
from src.server.services.report_service import report_service
from src.server.services.scheduler.jobs import (
    architecture_patrol,
    cleanup_patrol,
    leads_patrol,
    patrol,
    patrol_infra,
    sentinel_patrol,
    task_dispatcher,
    tech_debt_patrol,
)

logger = get_logger(__name__)

API_RETRY_POLICY = retry(
    stop=stop_after_attempt(6),
    wait=wait_chain(*[wait_fixed(m * 60) for m in [5, 15, 45, 120, 240]]),
    reraise=True,
)

DEFAULT_TIMEZONE = ZoneInfo("Asia/Taipei")
class SchedulerService:
    _instance = None
    _scheduler = None

    def __new__(cls) -> "SchedulerService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._scheduler = AsyncIOScheduler(job_defaults={'misfire_grace_time': 60})
        return cls._instance

    async def start(self) -> None:
        if self._scheduler and not self._scheduler.running:
            logger.info("🕒 Clockwork: Starting Lifecycle-Driven Scheduler Service...")
            self._scheduler.start()
            await self._schedule_jobs()
            try:
                from src.server.services.scheduler.jobs.leads_patrol import check_and_resume_dag
                await check_and_resume_dag(self)
            except Exception as e:
                logger.error(f"Failed to run L2 DAG catchup: {e}")
        else:
            logger.warning("Clockwork: Scheduler already running.")

    def shutdown(self) -> None:
        if self._scheduler and self._scheduler.running:
            logger.info("🛑 Clockwork: Shutting down Scheduler...")
            self._scheduler.shutdown()

    async def _update_last_run(self, job_id: str) -> None:
        """Persists the last run timestamp to the database."""
        try:
            from src.server.config.config import get_config
            from src.server.services.settings_service import SettingsService

            settings = SettingsService()
            config = get_config()
            env_prefix = config.archon_env
            if env_prefix and not env_prefix.endswith("_"):
                env_prefix += "_"
            db_key = f"{env_prefix}LAST_RUN_{job_id.upper()}"
            now_iso = datetime.now(UTC).isoformat()
            settings.set_setting(db_key, now_iso)
        except Exception as e:
            logger.error(f"Scheduler: Failed to update last run for {job_id}: {e}")

    async def _get_last_run(self, job_id: str) -> datetime | None:
        """Retrieves the last run timestamp from the database."""
        try:
            from src.server.config.config import get_config
            from src.server.services.settings_service import SettingsService

            settings = SettingsService()
            config = get_config()
            env_prefix = config.archon_env
            if env_prefix and not env_prefix.endswith("_"):
                env_prefix += "_"
            db_key = f"{env_prefix}LAST_RUN_{job_id.upper()}"
            val = settings.get_setting(db_key)
            if val:
                return datetime.fromisoformat(val.replace("Z", "+00:00"))
        except Exception:
            pass
        return None

    async def _should_run_local_only(self, job_id: str, trigger: CronTrigger | None = None) -> bool:
        from src.server.config.config import get_config
        config = get_config()
        if config.space_id is not None:
            return False
        return await self._should_run_daily(job_id, trigger=trigger)

    async def _should_run_daily(self, job_id: str, trigger: CronTrigger | None = None) -> bool:
        now_local = datetime.now(DEFAULT_TIMEZONE)
        if trigger:
            try:
                target_hour = int(str(trigger.fields[5]))
                target_minute = int(str(trigger.fields[6]))
                if now_local.hour < target_hour or (now_local.hour == target_hour and now_local.minute < target_minute):
                    return False

                target_days = str(trigger.fields[4]).lower()
                if target_days != "*":
                    current_day_name = now_local.strftime("%a").lower()
                    if current_day_name not in target_days:
                        return False
            except Exception:
                pass
        last_run = await self._get_last_run(job_id)
        if not last_run:
            return True
        return last_run.astimezone(DEFAULT_TIMEZONE).date() < now_local.date()

    async def _should_run_weekly(self, job_id: str, trigger: CronTrigger | None = None) -> bool:
        last_run = await self._get_last_run(job_id)
        if not last_run:
            return True

        # 修正: ISO 週以週一為起點，若 Catchup 發生在週一，會與下週日同屬一週而導致跳過。
        # 透過 +1 天將切割線移至週日，確保下週日能正常執行。
        last_run_shifted = last_run.astimezone(DEFAULT_TIMEZONE) + timedelta(days=1)
        now_shifted = datetime.now(DEFAULT_TIMEZONE) + timedelta(days=1)
        return last_run_shifted.isocalendar()[:2] < now_shifted.isocalendar()[:2]

    async def _should_run_monthly(self, job_id: str, trigger: CronTrigger | None = None) -> bool:
        last_run = await self._get_last_run(job_id)
        if not last_run:
            return True
        last_run_local = last_run.astimezone(DEFAULT_TIMEZONE)
        now_local = datetime.now(DEFAULT_TIMEZONE)
        return (last_run_local.year, last_run_local.month) < (now_local.year, now_local.month)

    async def _should_run_biweekly(self, job_id: str, trigger: CronTrigger | None = None) -> bool:
        last_run = await self._get_last_run(job_id)
        if not last_run:
            return True
        return (datetime.now(DEFAULT_TIMEZONE).date() - last_run.astimezone(DEFAULT_TIMEZONE).date()).days >= 13

    def _schedule_stateless(self, job_func: Callable[..., Any], job_id: str, delay_mins: int, interval_mins: int) -> None:
        if not self._scheduler:
            return
        next_run = datetime.now(UTC) + timedelta(minutes=delay_mins)
        self._scheduler.add_job(job_func, trigger=DateTrigger(run_date=next_run), id=f"{job_id}_initial")
        self._scheduler.add_job(
            job_func, trigger=IntervalTrigger(minutes=interval_mins), id=job_id, replace_existing=True, next_run_time=next_run + timedelta(minutes=interval_mins)
        )
        logger.info(f"✅ Scheduled Stateless: {job_id} (Start: +{delay_mins}m, Loop: {interval_mins}m)")

    async def _schedule_stateful_job(self, job_func: Callable[..., Any], job_id: str, delay_mins: int, check_func: Callable[..., Any], trigger: CronTrigger, skip_msg: str) -> None:
        if not self._scheduler:
            return
        async def wrapper() -> None:
            if await check_func(job_id, trigger=trigger):
                logger.info(f"🕒 Clockwork: Executing stateful job '{job_id}'")
                try:
                    await job_func()
                    await self._update_last_run(job_id)
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {e}")
                    raise
            else:
                logger.info(f"⏭️ Clockwork: Skipped '{job_id}' ({skip_msg})")
        run_time = datetime.now(UTC) + timedelta(minutes=delay_mins)
        self._scheduler.add_job(wrapper, trigger=DateTrigger(run_date=run_time), id=f"{job_id}_catchup", replace_existing=True)
        self._scheduler.add_job(wrapper, trigger=trigger, id=f"{job_id}_recurring", replace_existing=True)
        logger.info(f"✅ Scheduled Stateful: {job_id} (Catchup: +{delay_mins}m, Cron: {trigger})")

    def _trigger_stateful_daily_event(self, job_func: Callable[..., Any], job_id: str) -> None:
        if not self._scheduler:
            return
        async def wrapper() -> None:
            if await self._should_run_daily(job_id):
                logger.info(f"🔗 Event-Driven: Executing daily job '{job_id}'")
                try:
                    await job_func()
                    await self._update_last_run(job_id)
                except Exception as e:
                    logger.error(f"Job {job_id} failed: {e}")
                    raise
            else:
                logger.info(f"⏭️ Event-Driven: Skipped '{job_id}' (Already run today)")
        self._scheduler.add_job(wrapper, id=f"{job_id}_event", replace_existing=True)

    def _parse_dynamic_hf_time(self, config: Any, offset_hours: int) -> tuple[int, int]:
        start_str = config.hf_sleep_start
        try:
            sh, sm = map(int, start_str.split(":"))
        except Exception:
            sh, sm = 20, 18
        total_mins = (sh * 60 + sm - (offset_hours * 60)) % (24 * 60)
        return total_mins // 60, total_mins % 60

    async def _schedule_jobs(self) -> None:
        if not self._scheduler:
            return

        from src.server.schemas.settings import SchedulerConfig
        from src.server.services.settings_service import SettingsService
        try:
            raw_settings = SettingsService().get_all_settings()
            config = SchedulerConfig.model_validate(raw_settings)
        except Exception as e:
            logger.warning(f"Failed to parse SchedulerConfig, falling back to defaults: {e}")
            config = SchedulerConfig()

        # --- Category 1: Stateless Patrols ---
        self._schedule_stateless(self._run_system_probe, "system_probe", 1, config.system_probe_interval_mins)
        self._schedule_stateless(self._run_log_patrol, "log_patrol", 2, config.log_patrol_interval_mins)
        self._schedule_stateless(self._run_task_dispatcher, "task_dispatcher", 3, config.task_dispatcher_interval_mins)
        self._schedule_stateless(self._run_model_verification, "model_verification", 4, config.model_verification_interval_mins)
        self._schedule_stateless(self._run_meta_twin_audit, "meta_twin_audit", 4, config.meta_twin_audit_interval_mins)

        # --- Category 2: Stateful Daily Jobs ---
        await self._schedule_stateful_job(self._cleanup_system_probes, "system_probe_cleanup", 5, self._should_run_daily, CronTrigger(hour=config.system_probe_cleanup_hour, minute=config.system_probe_cleanup_minute, timezone=DEFAULT_TIMEZONE), "Already run today")
        await self._schedule_stateful_job(self._run_auto_fetch_leads, "alice_auto_fetch", 6, self._should_run_local_only, CronTrigger(day_of_week=config.alice_auto_fetch_days, hour=config.alice_auto_fetch_hour, minute=config.alice_auto_fetch_minute, timezone=DEFAULT_TIMEZONE), "Already run today")
        await self._schedule_stateful_job(self._run_prune_stale_leads, "prune_stale_leads", 15, self._should_run_daily, CronTrigger(hour=config.prune_stale_leads_hour, minute=config.prune_stale_leads_minute, timezone=DEFAULT_TIMEZONE), "Already run today")
        await self._schedule_stateful_job(self._analyze_token_usage, "token_analysis", 20, self._should_run_daily, CronTrigger(hour=config.token_analysis_hour, minute=config.token_analysis_minute, timezone=DEFAULT_TIMEZONE), "Already run today")
        await self._schedule_stateful_job(self._run_business_sentinel, "business_sentinel", 25, self._should_run_daily, CronTrigger(hour=config.business_sentinel_hour, minute=config.business_sentinel_minute, timezone=DEFAULT_TIMEZONE), "Already run today")

        # --- Category 3: Stateful Weekly / Monthly Jobs ---
        weekly_h, weekly_m = self._parse_dynamic_hf_time(config, 3)
        await self._schedule_stateful_job(self._run_weekly_executive_summary, "weekly_executive_summary", 38, self._should_run_weekly, CronTrigger(day_of_week=config.weekly_executive_summary_days, hour=weekly_h, minute=weekly_m, timezone=DEFAULT_TIMEZONE), "Already run this week")

        health_h, health_m = self._parse_dynamic_hf_time(config, 1)
        await self._schedule_stateful_job(self._run_architecture_health_audit, "architecture_health_audit", 40, self._should_run_weekly, CronTrigger(day_of_week=config.architecture_health_audit_days, hour=health_h, minute=health_m, timezone=DEFAULT_TIMEZONE), "Already run this week")

        await self._schedule_stateful_job(self._run_monthly_executive_summary, "monthly_executive_summary", 42, self._should_run_monthly, CronTrigger(day=config.monthly_summary_day, hour=config.monthly_summary_hour, minute=config.monthly_summary_minute, timezone=DEFAULT_TIMEZONE), "Already run this month")

        # --- Category 4: Stateful Bi-weekly Maintenance ---
        await self._schedule_stateful_job(self._run_infrastructure_audit, "infrastructure_audit", 48, self._should_run_biweekly, CronTrigger(day_of_week=config.maintenance_audit_days, hour=config.maintenance_audit_hour, minute=config.maintenance_audit_minute, timezone=DEFAULT_TIMEZONE), "Already run recently")
        await self._schedule_stateful_job(self._run_api_deprecation_scan, "api_deprecation_scan", 50, self._should_run_biweekly, CronTrigger(day_of_week=config.maintenance_audit_days, hour=config.maintenance_audit_hour, minute=config.maintenance_audit_minute, timezone=DEFAULT_TIMEZONE), "Already run recently")
        await self._schedule_stateful_job(self._run_tech_debt_audit, "tech_debt_audit", 45, self._should_run_biweekly, CronTrigger(day_of_week=config.maintenance_audit_days, hour=config.maintenance_audit_hour, minute=config.maintenance_audit_minute, timezone=DEFAULT_TIMEZONE), "Already run recently")
        await self._schedule_stateful_job(self._run_ssot_audit, "ssot_audit", 47, self._should_run_biweekly, CronTrigger(day_of_week=config.maintenance_audit_days, hour=config.maintenance_audit_hour, minute=config.maintenance_audit_minute, timezone=DEFAULT_TIMEZONE), "Already run recently")

    # Delegation Methods
    async def _run_system_probe(self) -> None: await patrol.run_system_probe()
    async def _run_log_patrol(self) -> None: await patrol.run_log_patrol()
    async def _cleanup_system_probes(self) -> None: await cleanup_patrol.cleanup_system_probes()
    async def _run_tech_debt_audit(self) -> None: await tech_debt_patrol.run_tech_debt_audit()
    async def _run_ssot_audit(self) -> None: await tech_debt_patrol.run_ssot_audit()
    async def _run_model_verification(self) -> None: await patrol.run_model_verification()
    async def _run_infrastructure_audit(self) -> None: await patrol_infra.run_infrastructure_audit()
    async def _run_prune_stale_leads(self) -> None: await leads_patrol.run_prune_stale_leads()
    async def _analyze_token_usage(self) -> None: await sentinel_patrol.analyze_token_usage()
    async def _run_business_sentinel(self) -> None: await sentinel_patrol.run_business_sentinel()
    async def run_business_sentinel(self) -> None: await sentinel_patrol.run_business_sentinel()
    @API_RETRY_POLICY
    async def _run_daily_executive_summary(self) -> None:
        await report_service.generate_daily_executive_summary()

    @API_RETRY_POLICY
    async def _run_weekly_executive_summary(self) -> None:
        await report_service.generate_weekly_executive_summary()

    @API_RETRY_POLICY
    async def _run_monthly_executive_summary(self) -> None:
        await report_service.generate_monthly_executive_summary()
    async def _run_api_deprecation_scan(self) -> None: await sentinel_patrol.run_api_deprecation_scan()
    async def _run_task_dispatcher(self) -> None: await task_dispatcher.run_task_dispatcher()
    async def _run_architecture_health_audit(self) -> None: await architecture_patrol.run_architecture_health_audit()

    @API_RETRY_POLICY
    async def _run_auto_fetch_leads(self) -> None:
        await leads_patrol.run_auto_fetch_leads()
        self._trigger_stateful_daily_event(self._run_daily_market_report, "bob_market_report")

    @API_RETRY_POLICY
    async def _run_daily_market_report(self) -> None:
        await leads_patrol.run_daily_market_report()
        self._trigger_stateful_daily_event(self._run_daily_executive_summary, "daily_executive_summary")

    async def _run_meta_twin_audit(self) -> None:
        from .system.meta_twin_service import meta_twin_service
        await meta_twin_service.run_telemetry_audit()

scheduler_service = SchedulerService()
