from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from apscheduler.triggers.cron import CronTrigger

from src.server.services.scheduler.jobs.patrol import is_hf_awake
from src.server.services.scheduler_service import scheduler_service


def test_is_hf_awake_boundary_conditions():
    """
    Test boundary conditions for Hugging Face Sleep Awareness (17:18 ~ 07:20 CST).
    """
    # 17:17 CST -> Awake (True)
    cst_17_17 = datetime(2026, 6, 8, 17, 17, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler.jobs.patrol.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_17_17
        assert is_hf_awake() is True

    # 17:18 CST -> Sleep (False)
    cst_17_18 = datetime(2026, 6, 8, 17, 18, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler.jobs.patrol.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_17_18
        assert is_hf_awake() is False

    # 07:20 CST -> Sleep (False)
    cst_07_20 = datetime(2026, 6, 8, 7, 20, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler.jobs.patrol.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_07_20
        assert is_hf_awake() is False

    # 07:21 CST -> Awake (True)
    cst_07_21 = datetime(2026, 6, 8, 7, 21, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler.jobs.patrol.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_07_21
        assert is_hf_awake() is True


@pytest.mark.asyncio
async def test_scheduler_jobs_configuration():
    """
    Verify scheduler jobs are configured using correct CronTriggers.
    """
    # Initialize scheduler configuration
    await scheduler_service._schedule_jobs()
    assert scheduler_service._scheduler is not None
    jobs = scheduler_service._scheduler.get_jobs()

    # Create mapping of job ids to their triggers
    job_triggers = {job.id: job.trigger for job in jobs}

    # Verify alice_auto_fetch specific cron schedule (CST 10:30, tue,fri,sat,sun -> hour=10, minute=30, day_of_week=tue,fri,sat,sun)
    alice_trigger = job_triggers.get("alice_auto_fetch_recurring")
    assert isinstance(alice_trigger, CronTrigger)
    assert str(alice_trigger.timezone) == "Asia/Taipei"

    hour_field = next(f for f in alice_trigger.fields if f.name == "hour")
    minute_field = next(f for f in alice_trigger.fields if f.name == "minute")
    day_of_week_field = next(f for f in alice_trigger.fields if f.name == "day_of_week")
    assert str(hour_field) == "10"
    assert str(minute_field) == "25"
    assert str(day_of_week_field) == "tue,wed,fri"

    # Verify token_analysis daily cron schedule (CST 08:20 -> hour=8, minute=20)
    token_trigger = job_triggers.get("token_analysis_recurring")
    assert isinstance(token_trigger, CronTrigger)
    assert str(token_trigger.timezone) == "Asia/Taipei"

    token_hour_field = next(f for f in token_trigger.fields if f.name == "hour")
    token_minute_field = next(f for f in token_trigger.fields if f.name == "minute")
    from src.server.schemas.settings import SchedulerConfig
    config = SchedulerConfig()
    assert str(token_hour_field) == str(config.dynamic_token_analysis_hour)
    assert str(token_minute_field) == str(config.dynamic_token_analysis_minute)

@pytest.mark.asyncio
async def test_should_run_daily_dynamic_reasons():
    from datetime import datetime, timedelta, timezone
    from unittest.mock import patch

    from apscheduler.triggers.cron import CronTrigger

    from src.server.services.scheduler_service import scheduler_service

    # 建立亞洲台北時區
    TAIPEI_TZ = timezone(timedelta(hours=8))

    trigger = CronTrigger(day_of_week='tue,wed,fri', hour=10, minute=25, timezone='Asia/Taipei')

    with patch("src.server.services.scheduler_service.datetime") as mock_datetime:
        # 情境 A: 當前時間 < 目標時間 (例如 09:05，禮拜二)
        mock_datetime.now.return_value = datetime(2026, 9, 1, 9, 5, tzinfo=TAIPEI_TZ) # 2026-09-01 is Tuesday
        with patch.object(scheduler_service, "_get_last_run", return_value=None):
            should_run, reason = await scheduler_service._should_run_daily("test_job", trigger)
            assert should_run is False
            assert "Time not reached" in reason

        # 情境 B: 非排程日 (例如 11:00，禮拜四)
        mock_datetime.now.return_value = datetime(2026, 9, 3, 11, 0, tzinfo=TAIPEI_TZ) # 2026-09-03 is Thursday
        with patch.object(scheduler_service, "_get_last_run", return_value=None):
            should_run, reason = await scheduler_service._should_run_daily("test_job", trigger)
            assert should_run is False
            assert "Not scheduled for thu" in reason

        # 情境 C: 同日重複觸發 (今日已執行)
        mock_datetime.now.return_value = datetime(2026, 9, 4, 11, 0, tzinfo=TAIPEI_TZ) # 2026-09-04 is Friday, time > 10:25
        last_run_time = datetime(2026, 9, 4, 10, 25, tzinfo=TAIPEI_TZ)
        with patch.object(scheduler_service, "_get_last_run", return_value=last_run_time):
            should_run, reason = await scheduler_service._should_run_daily("test_job", trigger)
            assert should_run is False
            assert "Already run today at" in reason

        # 情境 D: 正常觸發
        mock_datetime.now.return_value = datetime(2026, 9, 4, 11, 0, tzinfo=TAIPEI_TZ)
        last_run_time = datetime(2026, 9, 3, 10, 25, tzinfo=TAIPEI_TZ) # Yesterday
        with patch.object(scheduler_service, "_get_last_run", return_value=last_run_time):
            should_run, reason = await scheduler_service._should_run_daily("test_job", trigger)
            assert should_run is True
            assert reason == ""
