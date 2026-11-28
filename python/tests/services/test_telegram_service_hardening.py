from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.server.schemas.settings import NotificationConfig
from src.server.services.system.telegram_service import TelegramService, telegram_service


@pytest.mark.asyncio
async def test_get_config_async_timeout_retry():
    """
    Test that _get_config_async retries on database fetch timeout,
    does not crash the event loop, and eventually returns empty config while logging to DB.
    """
    with patch("src.server.services.system.telegram_service.get_supabase_client"), \
         patch("src.server.services.system.telegram_service.SettingsService") as MockSettingsService, \
         patch.object(telegram_service, "_log_to_db", new_callable=AsyncMock) as mock_log_db, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        # Mock SettingsService to always throw a TimeoutError
        mock_instance = MockSettingsService.return_value
        mock_instance.get_all_settings.side_effect = TimeoutError("Database connection timed out")

        # Execute
        config = await telegram_service._get_config_async()

        # Assertions
        assert isinstance(config, NotificationConfig)
        assert config.telegram_token is None
        assert config.telegram_chat_id is None

        # Verify it retried 3 times (call count = 3)
        assert mock_instance.get_all_settings.call_count == 3
        # Verify it slept 2 times (between the 3 attempts)
        assert mock_sleep.call_count == 2

        # Verify it logged to DB
        mock_log_db.assert_called_once()
        args, _ = mock_log_db.call_args
        assert args[0] == "ERROR"
        assert "Failed to fetch TELEGRAM_TOKEN" in args[1]


@pytest.mark.asyncio
async def test_send_message_network_error_logging():
    """
    Test that send_message logs to archon_logs after 3 failed network attempts.
    """
    with patch.object(telegram_service, "_get_config_async", new_callable=AsyncMock) as mock_get_config, \
         patch.object(telegram_service, "_log_to_db", new_callable=AsyncMock) as mock_log_db, \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        # Mock config to have valid tokens
        mock_config = NotificationConfig(**{"TELEGRAM_TOKEN": "fake_token", "TELEGRAM_TO": "fake_chat"})
        mock_get_config.return_value = mock_config

        # Mock post to throw RequestError
        mock_post.side_effect = httpx.RequestError("Network dropped")

        # Execute
        result = await telegram_service.send_message("Test message")

        # Assertions
        assert result is False
        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2

        # Verify it logged the final network error to DB
        mock_log_db.assert_called_once()
        args, _ = mock_log_db.call_args
        assert args[0] == "ERROR"
        assert "Network error sending message" in args[1]


@pytest.mark.asyncio
async def test_send_message_missing_token_logging():
    """
    Test that send_message logs to archon_logs if token is missing.
    """
    with patch.object(telegram_service, "_get_config_async", new_callable=AsyncMock) as mock_get_config, \
         patch.object(telegram_service, "_log_to_db", new_callable=AsyncMock) as mock_log_db:

        # Mock config to have missing tokens
        mock_config = NotificationConfig(telegram_token=None, telegram_chat_id=None)
        mock_get_config.return_value = mock_config

        # Execute
        result = await telegram_service.send_message("Test message")

        # Assertions
        assert result is False

        # Verify it logged the missing token to DB
        mock_log_db.assert_called_once()
        args, _ = mock_log_db.call_args
        assert args[0] == "ERROR"
        assert "TELEGRAM_TOKEN or TELEGRAM_TO not configured" in args[1]


def _delivery_config() -> NotificationConfig:
    return NotificationConfig.model_validate({
        "TELEGRAM_TOKEN": "fake-token",
        "TELEGRAM_TO": "fake-chat",
        "TELEGRAM_RETRIES": 1,
    })


def _capturing_client(captured: list[dict]) -> MagicMock:
    def insert(payload: dict) -> MagicMock:
        captured.append(payload)
        query = MagicMock()
        query.execute.return_value = MagicMock(data=[{"id": "log-1"}], count=None)
        return query

    table = MagicMock()
    table.insert.side_effect = insert
    empty = MagicMock()
    empty.execute.return_value = MagicMock(data=[], count=None)
    table.select.return_value.limit.return_value = empty
    client = MagicMock()
    client.table.return_value = table
    return client


def _ok_response(message_id: int) -> MagicMock:
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "ok": True,
        "result": {"message_id": message_id, "chat": {"id": 424242}},
    }
    return response


@pytest.mark.asyncio
async def test_daily_summary_delivery_writes_archon_log_with_message_id():
    """A recorded delivery writes one INFO archon_logs row that carries message_id only."""
    service = TelegramService()
    captured: list[dict] = []
    with patch.object(service, "_get_config_async", new_callable=AsyncMock) as mock_config, \
         patch("src.server.services.system.telegram_service.get_supabase_client", return_value=_capturing_client(captured)), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_config.return_value = _delivery_config()
        mock_post.return_value = _ok_response(9001)

        result = await service.send_message("daily summary body", record_delivery=True)

    assert result is True
    assert len(captured) == 1
    row = captured[0]
    assert row == {
        "source": "system-telegram",
        "level": "INFO",
        "message": "TelegramService: daily summary delivered",
        "details": {"message_id": 9001},
    }
    assert "fake-token" not in str(row)
    assert "fake-chat" not in str(row)
    assert "424242" not in str(row)


@pytest.mark.asyncio
async def test_send_success_without_record_delivery_does_not_write_log():
    """Callers other than the daily summary keep the previous success path: no archon_logs insert."""
    service = TelegramService()
    captured: list[dict] = []
    with patch.object(service, "_get_config_async", new_callable=AsyncMock) as mock_config, \
         patch("src.server.services.system.telegram_service.get_supabase_client", return_value=_capturing_client(captured)), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_config.return_value = _delivery_config()
        mock_post.return_value = _ok_response(9001)

        result = await service.send_message("sentinel alert")

    assert result is True
    assert captured == []


@pytest.mark.asyncio
async def test_network_error_archon_log_shape_unchanged():
    """Failure still writes one ERROR row with source, level, and message, and no details."""
    service = TelegramService()
    captured: list[dict] = []
    with patch.object(service, "_get_config_async", new_callable=AsyncMock) as mock_config, \
         patch("src.server.services.system.telegram_service.get_supabase_client", return_value=_capturing_client(captured)), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post, \
         patch("asyncio.sleep", new_callable=AsyncMock):
        mock_config.return_value = _delivery_config()
        mock_post.side_effect = httpx.RequestError("Network dropped")

        result = await service.send_message("daily summary body", record_delivery=True)

    assert result is False
    assert len(captured) == 1
    row = captured[0]
    assert set(row) == {"source", "level", "message"}
    assert row["source"] == "system-telegram"
    assert row["level"] == "ERROR"
    assert "Network error sending message" in row["message"]
    assert "daily summary delivered" not in row["message"]


@pytest.mark.asyncio
async def test_delivery_log_failure_does_not_fail_send():
    """A broken archon_logs insert does not change a successful Telegram send."""
    service = TelegramService()
    with patch.object(service, "_get_config_async", new_callable=AsyncMock) as mock_config, \
         patch(
             "src.server.services.system.telegram_service.get_supabase_client",
             side_effect=RuntimeError("supabase down"),
         ), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_config.return_value = _delivery_config()
        mock_post.return_value = _ok_response(9001)

        result = await service.send_message("daily summary body", record_delivery=True)

    assert result is True
    mock_post.assert_awaited_once()


@pytest.mark.asyncio
async def test_plain_text_fallback_delivery_log_includes_message_id():
    """Markdown recovery still records the delivered message_id and keeps the WARNING row."""
    service = TelegramService()
    captured: list[dict] = []
    resp_400 = MagicMock(status_code=400, text="can't parse entities")
    resp_400.request = httpx.Request("POST", "https://example.test/send")
    with patch.object(service, "_get_config_async", new_callable=AsyncMock) as mock_config, \
         patch("src.server.services.system.telegram_service.get_supabase_client", return_value=_capturing_client(captured)), \
         patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_config.return_value = _delivery_config()
        mock_post.side_effect = [
            httpx.HTTPStatusError("400", request=resp_400.request, response=resp_400),
            _ok_response(77),
        ]

        result = await service.send_message("broken *markdown", record_delivery=True)

    assert result is True
    info_rows = [row for row in captured if row["level"] == "INFO"]
    warning_rows = [row for row in captured if row["level"] == "WARNING"]
    assert info_rows == [{
        "source": "system-telegram",
        "level": "INFO",
        "message": "TelegramService: daily summary delivered",
        "details": {"message_id": 77},
    }]
    assert len(warning_rows) == 1
    assert warning_rows[0]["level"] == "WARNING"
    assert "details" not in warning_rows[0]
    assert "plain text fallback" in warning_rows[0]["message"]
