from unittest.mock import AsyncMock, MagicMock

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

    mock_execute_query = AsyncMock(return_value=(True, {"data": [{"id": "1", "message": "test"}, None, "invalid"]}))
    system_service.execute_query_async = mock_execute_query

    result = await system_service.list_connectivity_logs()
    assert len(result) == 1
    assert result[0]["id"] == "1"

@pytest.mark.asyncio
async def test_list_system_settings_success(system_service, mock_supabase):
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.order.return_value = mock_query

    mock_execute_query = AsyncMock(return_value=(True, {"data": [{"key": "test", "value": "1"}, None]}))
    system_service.execute_query_async = mock_execute_query

    result = await system_service.list_system_settings()
    assert len(result) == 1
    assert result[0]["key"] == "test"

@pytest.mark.asyncio
async def test_update_system_setting_success(system_service, mock_supabase):
    mock_query_old = MagicMock()
    mock_query_upd = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query_old
    mock_supabase.table.return_value.update.return_value.eq.return_value = mock_query_upd

    async def side_effect(query, error_msg, require_data=False):
        if query == mock_query_old:
            return True, {"data": [{"value": "old_value", "is_system_protected": False}]}
        elif query == mock_query_upd:
            return True, {"data": [{"key": "test", "value": "new_value", "updated_at": "now()"}]}
        return True, {}

    mock_execute_query = AsyncMock(side_effect=side_effect)
    system_service.execute_query_async = mock_execute_query

    result = await system_service.update_system_setting("test", "new_value", "desc", "user")
    assert result["key"] == "test"
    assert result["value"] == "new_value"

    # Verify physical schema alignment of the audit insert payload
    insert_call = mock_supabase.table.return_value.insert.call_args
    assert insert_call is not None
    audit_data = insert_call[0][0]
    assert audit_data["document_id"] == "setting:test"
    assert audit_data["field_name"] == "system_setting"
    assert "old_value" not in audit_data  # must NOT be top-level column in archon_document_versions
    assert "new_value" not in audit_data  # must NOT be top-level column in archon_document_versions
    assert audit_data["content"]["old_value"] == "old_value"
    assert audit_data["content"]["new_value"] == "new_value"

@pytest.mark.asyncio
async def test_update_system_setting_not_found(system_service, mock_supabase):
    mock_query_old = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query_old

    mock_execute_query = AsyncMock(return_value=(False, {}))
    system_service.execute_query_async = mock_execute_query

    with pytest.raises(ValueError):
        await system_service.update_system_setting("test", "new_value", "desc", "user")

@pytest.mark.asyncio
async def test_update_system_setting_malformed_data(system_service, mock_supabase):
    mock_query_old = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value = mock_query_old

    mock_execute_query = AsyncMock(return_value=(True, {"data": [None]}))
    system_service.execute_query_async = mock_execute_query

    with pytest.raises(ValueError, match="Setting 'test' not found"):
        await system_service.update_system_setting("test", "new_value", "desc", "user")
