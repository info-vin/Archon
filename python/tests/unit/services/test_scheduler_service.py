from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from apscheduler.triggers.cron import CronTrigger

from src.server.services.scheduler_service import is_hf_awake, scheduler_service


def test_is_hf_awake_boundary_conditions():
    """
    Test boundary conditions for Hugging Face Sleep Awareness (00:18 ~ 06:41 CST).
    """
    # 00:17 CST -> Awake (True)
    cst_00_17 = datetime(2026, 6, 8, 0, 17, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_00_17.astimezone(UTC)
        assert is_hf_awake() is True

    # 00:18 CST -> Sleep (False)
    cst_00_18 = datetime(2026, 6, 8, 0, 18, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_00_18.astimezone(UTC)
        assert is_hf_awake() is False

    # 06:41 CST -> Sleep (False)
    cst_06_41 = datetime(2026, 6, 8, 6, 41, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_06_41.astimezone(UTC)
        assert is_hf_awake() is False

    # 06:42 CST -> Awake (True)
    cst_06_42 = datetime(2026, 6, 8, 6, 42, tzinfo=timezone(timedelta(hours=8)))
    with patch("src.server.services.scheduler_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = cst_06_42.astimezone(UTC)
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

    # Verify alice_auto_fetch daily cron schedule (CST 07:00 -> hour=7, minute=0)
    alice_trigger = job_triggers.get("alice_auto_fetch_recurring")
    assert isinstance(alice_trigger, CronTrigger)
    assert str(alice_trigger.timezone) == "Asia/Taipei"

    hour_field = next(f for f in alice_trigger.fields if f.name == "hour")
    minute_field = next(f for f in alice_trigger.fields if f.name == "minute")
    assert str(hour_field) == "7"
    assert str(minute_field) == "0"

    # Verify token_analysis daily cron schedule (CST 08:20 -> hour=8, minute=20)
    token_trigger = job_triggers.get("token_analysis_recurring")
    assert isinstance(token_trigger, CronTrigger)
    assert str(token_trigger.timezone) == "Asia/Taipei"

    token_hour_field = next(f for f in token_trigger.fields if f.name == "hour")
    token_minute_field = next(f for f in token_trigger.fields if f.name == "minute")
    assert str(token_hour_field) == "8"
    assert str(token_minute_field) == "20"
