from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from apscheduler.triggers.cron import CronTrigger

from src.server.services.scheduler.jobs.patrol import is_hf_awake
from src.server.services.scheduler_service import scheduler_service


def test_is_hf_awake_boundary_conditions():
    """
    Test boundary conditions for Hugging Face Sleep Awareness (17:58 ~ 07:20 CST).
    """
    # 17:57 CST -> Awake (True)
    cst_17_57 = datetime(2026, 6, 8, 17, 57, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler.jobs.patrol.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_17_57
        assert is_hf_awake() is True

    # 17:58 CST -> Sleep (False)
    cst_17_58 = datetime(2026, 6, 8, 17, 58, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler.jobs.patrol.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_17_58
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
    assert str(day_of_week_field) == "tue,wed,thu,fri"

    # Verify token_analysis daily cron schedule (CST 08:20 -> hour=8, minute=20)
    token_trigger = job_triggers.get("token_analysis_recurring")
    assert isinstance(token_trigger, CronTrigger)
    assert str(token_trigger.timezone) == "Asia/Taipei"

    token_hour_field = next(f for f in token_trigger.fields if f.name == "hour")
    token_minute_field = next(f for f in token_trigger.fields if f.name == "minute")
    assert str(token_hour_field) == "8"
    assert str(token_minute_field) == "20"
