from unittest.mock import AsyncMock, MagicMock

import pytest

from src.server.services.log_service import LogDataDTO, LogService


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    return client

@pytest.fixture
def log_service(mock_supabase):
    service = LogService(mock_supabase)
    return service

def test_create_log_entry_success(log_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.insert.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"id": "1", "message": "test", "level": "INFO", "source": "system"}]}))
    log_service.execute_query = mock_execute_query

    log_data: LogDataDTO = {"user_input": "hello", "gemini_response": "hi"}
    success, result = log_service.create_log_entry(log_data)

    assert success is True
    assert "log" in result
    assert result["log"]["id"] == "1"

def test_create_log_entry_failure(log_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.insert.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(False, {"error": "DB error"}))
    log_service.execute_query = mock_execute_query

    log_data: LogDataDTO = {"user_input": "hello", "gemini_response": "hi"}
    success, result = log_service.create_log_entry(log_data)

    assert success is False
    assert result["error"] == "DB error"

def test_create_log_entry_empty_response_data(log_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.insert.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": []}))
    log_service.execute_query = mock_execute_query

    log_data: LogDataDTO = {"user_input": "hello", "gemini_response": "hi"}
    success, result = log_service.create_log_entry(log_data)

    assert success is False
    assert "Failed to insert log" in result["error"]

@pytest.mark.asyncio
async def test_record_interaction_success(log_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.insert.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"id": "1", "message": "test"}]}))
    log_service.execute_query = mock_execute_query

    log_data: LogDataDTO = {"user_input": "hello", "gemini_response": "hi"}
    result = await log_service.record_interaction("user123", log_data)

    assert "log" in result
    assert result["log"]["id"] == "1"

@pytest.mark.asyncio
async def test_get_active_alerts_success(log_service):
    mock_execute_query_async = AsyncMock(
        return_value=(
            True,
            {
                "data": [
                    {
                        "id": "alert-101",
                        "level": "ALERT",
                        "message": "High memory consumption detected",
                        "created_at": "2025-01-01T00:00:00Z",
                        "source": "threading_service",
                        "project_name": "system-resource",
                        "details": {"memory_percent": 95},
                    }
                ]
            },
        )
    )
    log_service.execute_query_async = mock_execute_query_async

    result = await log_service.get_active_alerts(limit=10)
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["id"] == "alert-101"
    assert result[0]["message"] == "High memory consumption detected"
    assert result[0]["level"] == "ALERT"

@pytest.mark.asyncio
async def test_get_active_alerts_error(log_service):
    mock_execute_query_async = AsyncMock(return_value=(False, {"error": "DB failure"}))
    log_service.execute_query_async = mock_execute_query_async

    result = await log_service.get_active_alerts(limit=10)
    assert isinstance(result, list)
    assert len(result) == 0

@pytest.mark.asyncio
async def test_get_recent_alerts_success(log_service):
    mock_execute_query_async = AsyncMock(return_value=(True, {"data": [{"id": "1", "level": "ALERT", "message": "High CPU"}]}))
    log_service.execute_query_async = mock_execute_query_async

    success, res = await log_service.get_recent_alerts(limit=5)
    assert success is True
    assert "data" in res
    assert len(res["data"]) == 1
    assert res["data"][0]["message"] == "High CPU"

@pytest.mark.asyncio
async def test_get_recent_alerts_failure(log_service):
    mock_execute_query_async = AsyncMock(return_value=(False, {"error": "Failed to fetch"}))
    log_service.execute_query_async = mock_execute_query_async

    success, res = await log_service.get_recent_alerts(limit=5)
    assert success is False
    assert "error" in res
    assert res["error"] == "Failed to fetch"
