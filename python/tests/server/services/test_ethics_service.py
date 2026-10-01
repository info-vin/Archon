from unittest.mock import AsyncMock, MagicMock

import pytest

from src.server.services.ethics_service import CreateEthicsEventDTO, EthicsService


@pytest.fixture
def mock_supabase():
    return MagicMock()


@pytest.fixture
def ethics_service(mock_supabase):
    return EthicsService(supabase_client=mock_supabase)


@pytest.mark.asyncio
async def test_get_ethics_events_success(ethics_service, mock_supabase):
    mock_execute_query_async = AsyncMock(
        return_value=(True, {"data": [{"id": "evt-1", "severity": "high", "event_type": "policy"}]})
    )
    ethics_service.execute_query_async = mock_execute_query_async

    events = await ethics_service.get_ethics_events(limit=10)
    assert len(events) == 1
    assert events[0]["id"] == "evt-1"
    assert events[0]["severity"] == "high"


@pytest.mark.asyncio
async def test_get_ethics_events_with_filters(ethics_service, mock_supabase):
    mock_execute_query_async = AsyncMock(
        return_value=(True, {"data": [{"id": "evt-2", "severity": "medium", "event_type": "leakage", "resolved": False}]})
    )
    ethics_service.execute_query_async = mock_execute_query_async

    events = await ethics_service.get_ethics_events(limit=5, severity="medium", resolved=False)
    assert len(events) == 1
    assert events[0]["id"] == "evt-2"


@pytest.mark.asyncio
async def test_get_ethics_events_failure(ethics_service, mock_supabase):
    mock_execute_query_async = AsyncMock(return_value=(False, {}))
    ethics_service.execute_query_async = mock_execute_query_async

    events = await ethics_service.get_ethics_events(limit=10)
    assert events == []


@pytest.mark.asyncio
async def test_get_ethics_event_by_id_success(ethics_service, mock_supabase):
    mock_execute_query_async = AsyncMock(
        return_value=(True, {"data": [{"id": "evt-100", "severity": "high", "event_type": "policy_violation"}]})
    )
    ethics_service.execute_query_async = mock_execute_query_async

    event = await ethics_service.get_ethics_event_by_id("evt-100")
    assert event is not None
    assert event["id"] == "evt-100"


@pytest.mark.asyncio
async def test_get_ethics_event_by_id_not_found(ethics_service, mock_supabase):
    mock_execute_query_async = AsyncMock(return_value=(True, {"data": []}))
    ethics_service.execute_query_async = mock_execute_query_async

    event = await ethics_service.get_ethics_event_by_id("non-existent")
    assert event is None


@pytest.mark.asyncio
async def test_create_ethics_event_success(ethics_service, mock_supabase):
    created_payload = {"id": "evt-200", "severity": "high", "event_type": "keyword_block", "created_at": "2025-01-01T00:00:00"}
    mock_execute_query_async = AsyncMock(return_value=(True, {"data": [created_payload]}))
    ethics_service.execute_query_async = mock_execute_query_async

    dto: CreateEthicsEventDTO = {
        "severity": "high",
        "event_type": "keyword_block",
        "created_at": "2025-01-01T00:00:00",
    }
    result = await ethics_service.create_ethics_event(dto)
    assert result is not None
    assert result["id"] == "evt-200"


@pytest.mark.asyncio
async def test_resolve_ethics_event_success(ethics_service, mock_supabase):
    resolved_payload = {
        "id": "evt-300",
        "severity": "medium",
        "event_type": "policy",
        "resolved": True,
        "resolution_notes": "Reviewed and cleared",
    }
    mock_execute_query_async = AsyncMock(return_value=(True, {"data": [resolved_payload]}))
    ethics_service.execute_query_async = mock_execute_query_async

    result = await ethics_service.resolve_ethics_event("evt-300", resolution_notes="Reviewed and cleared")
    assert result is not None
    assert result["resolved"] is True
    assert result["resolution_notes"] == "Reviewed and cleared"
