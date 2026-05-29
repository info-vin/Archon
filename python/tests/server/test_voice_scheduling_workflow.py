from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.server.schemas.agent_outputs import VoiceProcessResult
from src.server.services.stats import stats_service
from src.server.services.visit_log_service import visit_log_service


@pytest.mark.asyncio
async def test_scheduling_algorithm_availability():
    """
    Test stats_service.get_team_availability calculation.
    Mocks DB responses to simulate Bob & Charlie busy times and asserts correct recommendations in local GMT+8 time.
    """
    target_date = "2026-06-01"
    user_ids = ["bob-uuid-123", "charlie-uuid-456"]

    # Mock Supabase data returning Bob & Charlie busy slots in local GMT+8 time
    # Bob: 09:00 - 11:00 GMT+8 (due 11:00, 2 hrs estimate)
    # Charlie: 14:00 - 15:00 GMT+8 (due 15:00, 1 hr estimate)
    mock_tasks = [
        {
            "assignee_id": "bob-uuid-123",
            "due_date": f"{target_date}T11:00:00+08:00",
            "estimated_hours": 2.0,
            "status": "todo"
        },
        {
            "assignee_id": "charlie-uuid-456",
            "due_date": f"{target_date}T15:00:00+08:00",
            "estimated_hours": 1.0,
            "status": "doing"
        }
    ]

    mock_res = MagicMockResponse(mock_tasks)

    # Patch system_metrics supabase select table queries
    with patch.object(stats_service.metrics.system_metrics.supabase, "table") as mock_table:
        mock_table.return_value.select.return_value.in_.return_value.neq.return_value.or_.return_value.gte.return_value.lte.return_value.execute = MagicMockExecutor(mock_res)

        slots = await stats_service.get_team_availability(user_ids, target_date)

        assert len(slots) == 3
        # Assertions to verify slots are outside busy ranges
        for slot in slots:
            st = datetime.fromisoformat(slot["start_time"])
            et = datetime.fromisoformat(slot["end_time"])

            # Should not intersect with Bob: 09:00-11:00
            bob_start = datetime.fromisoformat(f"{target_date}T09:00:00+08:00")
            bob_end = datetime.fromisoformat(f"{target_date}T11:00:00+08:00")
            assert not (st < bob_end and et > bob_start)

            # Should not intersect with Charlie: 14:00-15:00
            charlie_start = datetime.fromisoformat(f"{target_date}T14:00:00+08:00")
            charlie_end = datetime.fromisoformat(f"{target_date}T15:00:00+08:00")
            assert not (st < charlie_end and et > charlie_start)


@pytest.mark.asyncio
async def test_fragile_date_parsing_robustness():
    """
    Verifies that system_metrics cleanly extracts YYYY-MM-DD from dirty dates
    (e.g., "2026-06-01 (下週一)" or with surrounding text) instead of crashing.
    """
    dirty_date = "2026-06-01 (下週一)"
    user_ids = ["bob-uuid-123", "charlie-uuid-456"]
    mock_res = MagicMockResponse([])

    with patch.object(stats_service.metrics.system_metrics.supabase, "table") as mock_table:
        mock_table.return_value.select.return_value.in_.return_value.neq.return_value.or_.return_value.gte.return_value.lte.return_value.execute = MagicMockExecutor(mock_res)

        # Should parse clean date and return fallback or empty slots instead of raising exception
        slots = await stats_service.get_team_availability(user_ids, dirty_date)
        assert len(slots) == 3
        # Verify clean date is used in slots
        assert slots[0]["start_time"].startswith("2026-06-01")


@pytest.mark.asyncio
async def test_end_to_end_voice_scheduling_integration():
    """
    Test E2E voice scheduling path in VisitLogService.create_log.
    Mocks AI transcription response to include a scheduling intent and date.
    Verifies that the appropriate task is dispatched and recommendation returned.
    """
    # 1. Setup mock payload and mock AI response
    data = {
        "user_id": "user-alice-111",
        "company_name": "ACME Corp",
        "customer_id": "cust-999",
        "latitude": 25.0339,
        "longitude": 121.5645,
        "location_address": "Taipei 101"
    }

    mock_ai_res_dict = {
        "transcript": "我想預約下次 2026-06-01 跟 Bob 與 Charlie 的會議",
        "summary": "預約下次會議",
        "tasks": ["預約下次會議"],
        "scheduling_intent": True,
        "requested_date": "2026-06-01",
        "requested_duration_hours": 1.0,
        "meeting_topic": "需求規格書討論"
    }

    mock_parsed_ai_res = VoiceProcessResult(**mock_ai_res_dict)

    # Mock audio file upload
    class MockAudioFile:
        content_type = "audio/wav"
        async def read(self):
            return b"fake-audio-bytes"

    mock_audio = MockAudioFile()

    # Stub VisitLogService database insert
    mock_log_db_res = [{"id": "log-uuid-777", "summary": "預約下次會議"}]

    # Stub task service and agent resolver
    with patch.object(visit_log_service, "_process_voice_with_ai", AsyncMock(return_value=(
        mock_parsed_ai_res.transcript,
        mock_parsed_ai_res.summary,
        mock_parsed_ai_res.tasks,
        mock_parsed_ai_res
    ))), \
    patch.object(visit_log_service, "execute_query", return_value=(True, mock_log_db_res)), \
    patch("src.server.services.agent_registry.get_agent_uuid", side_effect=lambda key: f"{key}-uuid-mock"), \
    patch("src.server.services.projects.task_service.task_service.create_task", AsyncMock(return_value=(True, {}))) as mock_create_task:

        # Let's mock the archon_projects query in supabase client inside create_log
        mock_project_db = MagicMockResponse([{"id": "project-uuid-mock"}])
        with patch.object(visit_log_service.supabase_client, "table") as mock_table:
            # For project lookups
            mock_table.return_value.select.return_value.ilike.return_value.limit.return_value.execute = MagicMockExecutor(mock_project_db)

            success, log_res = await visit_log_service.create_log(data, mock_audio)

            # 2. Assertions
            assert success is True
            assert "scheduling_recommendation" in log_res
            rec = log_res["scheduling_recommendation"]
            assert rec["meeting_topic"] == "需求規格書討論"
            assert len(rec["suggested_slots"]) == 3

            # Assert task was created and dispatched to Bob with Charlie as collaborator
            mock_create_task.assert_called_once()
            args, kwargs = mock_create_task.call_args
            assert kwargs["project_id"] == "project-uuid-mock"
            assert "[待確認會議]" in kwargs["title"]
            assert kwargs["assignee_id"] == "market-bot-uuid-mock"
            assert "supervisor-uuid-mock" in kwargs["collaborator_agent_ids"]


# Helpers for mocking Supabase client executes
class MagicMockResponse:
    def __init__(self, data):
        self.data = data


class MagicMockExecutor:
    def __init__(self, response):
        self.response = response

    def __call__(self, *args, **kwargs):
        return self.response
