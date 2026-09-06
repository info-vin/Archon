from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.server.services.system.telegram_service import telegram_service


@pytest.mark.asyncio
async def test_telegram_service_uses_ipv4_transport():
    """
    Test that TelegramService uses a custom httpx.AsyncHTTPTransport
    with local_address="0.0.0.0" to prevent IPv6 blackhole timeouts.
    """
    mock_config = MagicMock()
    mock_config.telegram_token = "fake_token"
    mock_config.telegram_chat_id = "fake_chat_id"

    with patch.object(telegram_service, "_get_config_async", new_callable=AsyncMock) as mock_get_config:
        mock_get_config.return_value = mock_config
        # Mock httpx.AsyncClient to inspect how it's instantiated
        with patch("src.server.services.system.telegram_service.httpx.AsyncClient") as mock_async_client_class:
            # Setup the async context manager returned by AsyncClient()
            mock_client_instance = MagicMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None

            # Setup the post response
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            mock_async_client_class.return_value = mock_client_instance

            # Execute the send_message method
            result = await telegram_service.send_message("Test message")

            # Verify the message was "sent" successfully
            assert result is True

            # The critical check: Verify AsyncClient was instantiated with our custom transport
            mock_async_client_class.assert_called()

            # Get the kwargs used to instantiate AsyncClient
            _, kwargs = mock_async_client_class.call_args

            assert "transport" in kwargs, "AsyncClient must be instantiated with a custom transport"
            assert "timeout" in kwargs, "AsyncClient must have a timeout specified"
            assert kwargs["timeout"] == 30.0, "Timeout must be 30.0 seconds"

            transport = kwargs["transport"]
            assert isinstance(transport, httpx.AsyncHTTPTransport), "Transport must be httpx.AsyncHTTPTransport"

            # Check the local_address binding
            assert transport._pool._local_address == "0.0.0.0", "Transport must be bound to 0.0.0.0 to prevent IPv6 blackholes"

