
import inspect

from src.server.services.scheduler.jobs import leads_patrol
from src.server.services.scheduler_service import SchedulerService


def test_alice_is_interval_trigger():
    """Verify alice_auto_fetch uses IntervalTrigger(hours=12) instead of CronTrigger"""
    service = SchedulerService()

    # We can inspect the source code of _schedule_jobs
    source = inspect.getsource(service._schedule_jobs)

    # Simple substring check is enough to ensure it's not a CronTrigger anymore
    assert "IntervalTrigger(hours=12)" in source, "alice_auto_fetch should use IntervalTrigger(hours=12)"
    assert "alice_auto_fetch" in source
    assert "CronTrigger(day_of_week=config.alice_auto_fetch_days" not in source, "Alice must not be triggered strictly by days of week anymore"

def test_daily_executive_summary_is_decoupled_from_alice():
    """Verify that daily_executive_summary is its own CronTrigger and NOT in the DAG chain"""
    service = SchedulerService()
    source = inspect.getsource(service._schedule_jobs)

    # daily_executive_summary should be explicitly scheduled in _schedule_jobs as Category 2
    assert "await self._schedule_stateful_job(self._run_daily_executive_summary," in source, "daily_executive_summary must be an independent scheduled job now"
    assert "daily_executive_summary" in source

    # check that _run_market_report doesn't trigger executive summary
    run_market_report_source = inspect.getsource(service._run_market_report)
    assert "_trigger_stateful_daily_event" not in run_market_report_source, "Bob's market report must NOT trigger the daily executive summary"

def test_dag_catchup_is_decoupled():
    """Verify that check_and_resume_dag does not contain daily_executive_summary"""
    source = inspect.getsource(leads_patrol.check_and_resume_dag)
    assert "daily_executive_summary" not in source, "check_and_resume_dag must not catchup daily_executive_summary as it is decoupled"

def test_market_report_dynamic_fetch():
    """Verify run_market_report fetches dynamically based on LAST_RUN_BOB_MARKET_REPORT"""
    source = inspect.getsource(leads_patrol.run_market_report)
    assert "LAST_RUN_BOB_MARKET_REPORT" in source, "Bob must fetch dynamically based on his last run date"
    assert "one_day_ago" not in source, "Hardcoded one_day_ago must be removed"
