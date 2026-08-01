import pytest
from unittest.mock import MagicMock
from src.server.services.log_service import LogService, LogDataDTO

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

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"id": "1", "message": "test"}]}))
    log_service.execute_query = mock_execute_query

    log_data: LogDataDTO = {"user_input": "hello", "gemini_response": "hi"}
    success, result = log_service.create_log_entry(log_data)

    assert success is True
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
async def test_get_active_alerts(log_service):
    result = await log_service.get_active_alerts()
    assert isinstance(result, list)
    assert len(result) == 0
