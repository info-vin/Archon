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

    # Verify alice_auto_fetch uses IntervalTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    alice_trigger = job_triggers.get("alice_auto_fetch_recurring")
    assert isinstance(alice_trigger, IntervalTrigger)
    assert alice_trigger.interval.total_seconds() == 12 * 3600

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

    # Verify monthly_jules_compaction monthly cron schedule (day=1, hour=9, minute=30)
    jules_trigger = job_triggers.get("monthly_jules_compaction_recurring")
    assert isinstance(jules_trigger, CronTrigger)
    assert str(jules_trigger.timezone) == "Asia/Taipei"
    jules_day_field = next(f for f in jules_trigger.fields if f.name == "day")
    jules_hour_field = next(f for f in jules_trigger.fields if f.name == "hour")
    jules_minute_field = next(f for f in jules_trigger.fields if f.name == "minute")
    assert str(jules_day_field) == str(config.monthly_jules_compaction_day)
    assert str(jules_hour_field) == str(config.monthly_jules_compaction_hour)
    assert str(jules_minute_field) == str(config.monthly_jules_compaction_minute)

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


@pytest.mark.asyncio
async def test_run_monthly_jules_compaction_physical(tmp_path, mock_supabase_db):
    """
    Physical disk and stateful DB test for run_monthly_jules_compaction:
    Verifies hallucinated dates are stripped, duplicate blocks are deduplicated,
    entries are capped at 5 core rules per file, and a real row is inserted into archon_logs
    without mocking LogService.create_log_entry.
    """
    from src.server.services.log_service import LogService
    from src.server.services.scheduler.jobs import jules_compaction
    from src.server.services.scheduler.jobs.jules_compaction import (
        run_monthly_jules_compaction,
    )

    # Bind log_service to the stateful in-memory database (no method mocking!)
    jules_compaction.log_service = LogService(supabase_client=mock_supabase_db)

    sample_md = tmp_path / "type_guardian.md"
    sample_md.write_text(
        "# TypeGuardian Guidelines (Consolidated)\n\n"
        "## 2024-05-18 - Rule Alpha\n"
        "**Learning:** First learning.\n\n"
        "## 2023-11-02 - Rule Alpha\n"
        "**Learning:** Duplicate title should be removed.\n\n"
        "## 2025-01-10 - Rule Beta\n"
        "**Learning:** Second learning.\n\n"
        "## Rule Gamma\n"
        "**Learning:** Second learning.\n\n"
        "## 4. Rule Delta\n"
        "**Learning:** Third unique learning.\n\n"
        "## 2024-05-19 - Rule Epsilon\n"
        "**Learning:** Fourth unique learning.\n\n"
        "## 2024-05-20 - Rule Zeta\n"
        "**Learning:** Fifth unique learning.\n\n"
        "## 2024-05-21 - Rule Eta (Excess 6th Rule)\n"
        "**Learning:** Sixth unique learning should be truncated.\n",
        encoding="utf-8",
    )

    stats = await run_monthly_jules_compaction(jules_dir=tmp_path)
    assert stats["files_scanned"] == 1
    assert stats["files_modified"] == 1
    assert stats["entries_before"] == 8
    assert stats["entries_after"] == 5

    # Query archon_logs table directly to verify real LogService.create_log_entry execution
    logs_rows = mock_supabase_db.table("archon_logs").select("*").execute().data
    assert len(logs_rows) == 1
    log_row = logs_rows[0]
    assert log_row["source"] == "clockwork-scheduler"
    assert log_row["level"] == "INFO"
    assert log_row["details"]["user_input"] == "monthly_jules_compaction"
    assert "entries 8 -> 5" in log_row["message"]

    compacted = sample_md.read_text(encoding="utf-8")
    assert "2024-05-18" not in compacted
    assert "2023-11-02" not in compacted
    assert "2025-01-10" not in compacted
    assert "## 1. Rule Alpha" in compacted
    assert "## 2. Rule Beta" in compacted
    assert "## 3. Rule Delta" in compacted
    assert "## 4. Rule Epsilon" in compacted
    assert "## 5. Rule Zeta" in compacted
    assert "Rule Eta" not in compacted

    # Running a second time on already-compacted files should be idempotent (0 modified)
    stats_second = await run_monthly_jules_compaction(jules_dir=tmp_path)
    assert stats_second["files_modified"] == 0
    assert len(mock_supabase_db.table("archon_logs").select("*").execute().data) == 2


