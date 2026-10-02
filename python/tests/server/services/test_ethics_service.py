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
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.order.return_value.limit.return_value = mock_query

    mock_execute_query = AsyncMock(return_value=(True, {"data": [{"id": "evt-1", "severity": "high", "event_type": "policy"}]}))
    ethics_service.execute_query_async = mock_execute_query

    events = await ethics_service.get_ethics_events(limit=10)
    assert len(events) == 1
    assert events[0]["id"] == "evt-1"
    assert events[0]["severity"] == "high"


@pytest.mark.asyncio
async def test_get_ethics_events_failure(ethics_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.order.return_value.limit.return_value = mock_query

    mock_execute_query = AsyncMock(return_value=(False, {}))
    ethics_service.execute_query_async = mock_execute_query

    events = await ethics_service.get_ethics_events(limit=10)
    assert events == []


@pytest.mark.asyncio
async def test_create_ethics_event_success(ethics_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.insert.return_value = mock_query

    mock_execute_query = AsyncMock(
        return_value=(True, {"data": [{"id": "evt-2", "severity": "medium", "event_type": "policy_violation"}]})
    )
    ethics_service.execute_query_async = mock_execute_query

    payload: CreateEthicsEventDTO = {
        "severity": "medium",
        "event_type": "policy_violation",
        "description": "Test violation",
        "raw_input": "bad word",
    }
    result = await ethics_service.create_ethics_event(payload)
    assert result is not None
    assert result["id"] == "evt-2"
    assert result["severity"] == "medium"


@pytest.mark.asyncio
async def test_create_ethics_event_failure(ethics_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.insert.return_value = mock_query

    mock_execute_query = AsyncMock(return_value=(False, {}))
    ethics_service.execute_query_async = mock_execute_query

    payload: CreateEthicsEventDTO = {
        "severity": "medium",
        "event_type": "policy_violation",
    }
    result = await ethics_service.create_ethics_event(payload)
    assert result is None


@pytest.mark.asyncio
async def test_resolve_ethics_event_success(ethics_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value = mock_query

    mock_execute_query = AsyncMock(
        return_value=(True, {"data": [{"id": "evt-1", "resolved": True, "resolution_notes": "Resolved by admin"}]})
    )
    ethics_service.execute_query_async = mock_execute_query

    result = await ethics_service.resolve_ethics_event("evt-1", "Resolved by admin")
    assert result is not None
    assert result["id"] == "evt-1"
    assert result["resolved"] is True
    assert result["resolution_notes"] == "Resolved by admin"


@pytest.mark.asyncio
async def test_resolve_ethics_event_failure(ethics_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.update.return_value.eq.return_value = mock_query

    mock_execute_query = AsyncMock(return_value=(False, {}))
    ethics_service.execute_query_async = mock_execute_query

    result = await ethics_service.resolve_ethics_event("evt-1")
    assert result is None
