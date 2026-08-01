from unittest.mock import MagicMock

import pytest

from src.server.services.system_service import SystemService


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    return client

@pytest.fixture
def system_service(mock_supabase):
    service = SystemService()
    service.supabase_client = mock_supabase
    return service

@pytest.mark.asyncio
async def test_list_connectivity_logs(system_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"id": "1", "message": "test"}]}))
    system_service.execute_query = mock_execute_query

    result = await system_service.list_connectivity_logs()
    assert len(result) == 1
    assert result[0]["id"] == "1"

@pytest.mark.asyncio
async def test_list_system_settings_success(system_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.order.return_value = mock_query

    mock_execute_query = MagicMock(return_value=(True, {"data": [{"key": "test", "value": "1"}]}))
    system_service.execute_query = mock_execute_query

    result = await system_service.list_system_settings()
    assert len(result) == 1
    assert result[0]["key"] == "test"

@pytest.mark.asyncio
async def test_update_system_setting_success(system_service, mock_supabase):
    mock_query_old = MagicMock()
    mock_query_upd = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query_old
    mock_supabase.table.return_value.update.return_value.eq.return_value = mock_query_upd

    def side_effect(query, error_msg, require_data=False):
        if query == mock_query_old:
            return True, {"data": [{"value": "old_value", "is_system_protected": False}]}
        elif query == mock_query_upd:
            return True, {"data": [{"key": "test", "value": "new_value", "updated_at": "now()"}]}
        return True, {}

    mock_execute_query = MagicMock(side_effect=side_effect)
    system_service.execute_query = mock_execute_query

    result = await system_service.update_system_setting("test", "new_value", "desc", "user")
    assert result["key"] == "test"
    assert result["value"] == "new_value"

@pytest.mark.asyncio
async def test_update_system_setting_not_found(system_service, mock_supabase):
    mock_query_old = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query_old

    mock_execute_query = MagicMock(return_value=(False, {}))
    system_service.execute_query = mock_execute_query

    with pytest.raises(ValueError):
        await system_service.update_system_setting("test", "new_value", "desc", "user")
