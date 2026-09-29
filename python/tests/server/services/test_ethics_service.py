from unittest.mock import MagicMock

import pytest

from src.server.services.ethics_service import EthicsService


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

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"id": "evt-1", "severity": "high", "event_type": "policy"}]}))
    ethics_service.execute_query = mock_execute_query

    events = await ethics_service.get_ethics_events(limit=10)
    assert len(events) == 1
    assert events[0]["id"] == "evt-1"
    assert events[0]["severity"] == "high"


@pytest.mark.asyncio
async def test_get_ethics_events_failure(ethics_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.order.return_value.limit.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(False, {}))
    ethics_service.execute_query = mock_execute_query

    events = await ethics_service.get_ethics_events(limit=10)
    assert events == []
