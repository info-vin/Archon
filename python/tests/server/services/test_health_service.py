from unittest.mock import MagicMock

import pytest

from src.server.services.health_service import HealthService


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    return client

@pytest.fixture
def health_service(mock_supabase):
    service = HealthService()
    service.supabase_client = mock_supabase
    return service

def test_check_db_health(health_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.limit.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {}))
    health_service.execute_query = mock_execute_query

    assert health_service.check_db_health() is True

def test_verify_auth_config_success(health_service, mock_supabase):
    mock_supabase.auth = MagicMock()
    assert health_service.verify_auth_config() is True

def test_verify_auth_config_failure(health_service, mock_supabase):
    mock_supabase.auth = None
    assert health_service.verify_auth_config() is False

@pytest.mark.asyncio
async def test_get_health_history(health_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.gt.return_value.order.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [
        {"created_at": "2023-01-01T12:00:00Z", "details": {"score": 95.0}},
        {"created_at": "2023-01-02T12:00:00Z", "details": '{"score": 90.0}'}
    ]}))
    health_service.execute_query = mock_execute_query

    result = await health_service.get_health_history()
    assert len(result["trend"]) == 2
    assert result["trend"][0]["score"] == 95.0
    assert result["trend"][1]["score"] == 90.0
