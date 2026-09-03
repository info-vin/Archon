from unittest.mock import AsyncMock, patch

import httpx
import pytest

from src.server.schemas.settings import NotificationConfig
from src.server.services.system.telegram_service import telegram_service


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
