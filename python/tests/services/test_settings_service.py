import json
from unittest.mock import MagicMock

import pytest

from src.server.services.settings_service import SettingsService


@pytest.fixture
def mock_supabase():
    mock_client = MagicMock()
    return mock_client


def test_get_database_statistics_success(mock_supabase):
    service = SettingsService(supabase_client=mock_supabase)

    # Mock responses for each table count query
    table_mock = MagicMock()
    select_mock = MagicMock()
    table_mock.select.return_value = select_mock
    mock_supabase.table.return_value = table_mock

    # execute_query returns (success, result)
    service.execute_query = MagicMock(return_value=(True, {"count": 5}))

    success, result = service.get_database_statistics()

    assert success is True
    assert isinstance(result, dict)
    assert result["projects"] == 5
    assert result["tasks"] == 5
    assert result["crawled_pages"] == 5
    assert result["settings"] == 5


def test_get_database_statistics_failure(mock_supabase):
    service = SettingsService(supabase_client=mock_supabase)
    service.execute_query = MagicMock(return_value=(False, {"error": "DB error"}))

    success, result = service.get_database_statistics()

    assert success is False
    assert result == "DB error"


def test_get_setting_success(mock_supabase):
    service = SettingsService(supabase_client=mock_supabase)
    service.execute_query = MagicMock(return_value=(True, {"data": [{"value": "test_val"}]}))

    val = service.get_setting("test_key")
    assert val == "test_val"


def test_get_setting_fallback(mock_supabase):
    service = SettingsService(supabase_client=mock_supabase)
    service.execute_query = MagicMock(return_value=(False, {}))

    val = service.get_setting("non_existent", default="default_val")
    assert val == "default_val"


def test_get_all_settings(mock_supabase):
    service = SettingsService(supabase_client=mock_supabase)
    service.execute_query = MagicMock(
        return_value=(True, {"data": [{"key": "k1", "value": "v1"}, {"key": "k2", "value": "v2"}]})
    )

    settings = service.get_all_settings()
    assert settings == {"k1": "v1", "k2": "v2"}


def test_set_setting(mock_supabase):
    service = SettingsService(supabase_client=mock_supabase)
    service.execute_query = MagicMock(return_value=(True, {}))

    success = service.set_setting("k1", "v1")
    assert success is True


@pytest.mark.asyncio
async def test_upsert_setting(mock_supabase):
    service = SettingsService(supabase_client=mock_supabase)
    service.execute_query_async = MagicMock()

    # Create an awaitable return value for execute_query_async
    async def async_return():
        return True, {}

    service.execute_query_async.side_effect = lambda *args, **kwargs: async_return()

    success = await service.upsert_setting({"key": "k1", "value": "v1"})
    assert success is True


def test_check_and_increment_notebooklm_quota(mock_supabase):
    service = SettingsService(supabase_client=mock_supabase)

    # Initial state: no usage logged yet
    service.get_setting = MagicMock(return_value=None)
    service.set_setting = MagicMock(return_value=True)

    allowed = service.check_and_increment_notebooklm_quota()
    assert allowed is True
    service.set_setting.assert_called_once()

    # State: 9 usages logged -> quota reached
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    service.get_setting = MagicMock(return_value=json.dumps({"date": today, "count": 9}))
    allowed_at_limit = service.check_and_increment_notebooklm_quota()
    assert allowed_at_limit is False
