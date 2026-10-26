from unittest.mock import MagicMock, patch

import pytest

from src.server.schemas.settings import NotificationConfig
from src.server.services.system.telegram_service import telegram_service


@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.TelegramService._get_config_async")
@patch("httpx.AsyncClient.post")
async def test_telegram_proxy_routing(mock_post, mock_get_config):
    # Setup mock config with proxy
    mock_get_config.return_value = NotificationConfig.model_validate({
        "TELEGRAM_TOKEN": "fake_token",
        "TELEGRAM_TO": "fake_chat",
        "TELEGRAM_PROXY_URL": "https://archon-enduser.vercel.app/api/telegram"
    })

    # Setup mock response (httpx.Response.raise_for_status is synchronous)
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    # Send message
    success = await telegram_service.send_message("Test Proxy")

    # Verify success
    assert success is True

    # Assert Route and Payload Integrity
    assert mock_post.called
    call_args, call_kwargs = mock_post.call_args

    # 1. Assert Target URL (Must not be api.telegram.org)
    assert call_args[0] == "https://archon-enduser.vercel.app/api/telegram"
    assert "api.telegram.org" not in call_args[0]

    # 2. Assert Payload Integrity (Must include bot_token)
    payload = call_kwargs.get("json", {})
    assert payload.get("bot_token") == "fake_token"
    assert payload.get("chat_id") == "fake_chat"
    assert payload.get("text") == "Test Proxy"

@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.TelegramService._get_config_async")
@patch("httpx.AsyncClient.post")
async def test_telegram_direct_fallback(mock_post, mock_get_config):
    # Setup mock config WITHOUT proxy (local dev fallback)
    mock_get_config.return_value = NotificationConfig.model_validate({
        "TELEGRAM_TOKEN": "fake_token",
        "TELEGRAM_TO": "fake_chat"
    })

    # Setup mock response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    # Send message
    success = await telegram_service.send_message("Test Direct")

    # Verify success
    assert success is True

    # Assert Route and Payload Integrity
    assert mock_post.called
    call_args, call_kwargs = mock_post.call_args

    # 1. Assert Target URL (Must be direct)
    assert call_args[0] == "https://api.telegram.org/botfake_token/sendMessage"

    # 2. Assert Payload (Must NOT include bot_token in payload)
    payload = call_kwargs.get("json", {})
    assert "bot_token" not in payload
    assert payload.get("chat_id") == "fake_chat"
    assert payload.get("text") == "Test Direct"


@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.TelegramService._get_config_async")
@patch("httpx.AsyncClient.post")
async def test_telegram_send_voice_proxy_first_and_direct_fallback(mock_post, mock_get_config):
    import httpx

    mock_get_config.return_value = NotificationConfig.model_validate({
        "TELEGRAM_TOKEN": "fake_token",
        "TELEGRAM_TO": "fake_chat",
        "TELEGRAM_PROXY_URL": "https://archon-enduser.vercel.app/api/telegram",
        "TELEGRAM_RETRIES": 1,
    })

    # First call (Proxy) raises network error, second call (Direct sendVoice) succeeds
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_post.side_effect = [
        httpx.ConnectTimeout("Proxy unreachable"),
        mock_resp,
    ]

    voice_data = b"RIFF_FAKE_WAV_BYTES"
    success = await telegram_service.send_voice(voice_data, caption="🎙️ Voice Test")

    assert success is True
    assert mock_post.call_count == 2
    # First attempt must be Proxy (to avoid 30s HF firewall drop on api.telegram.org)
    first_args, first_kwargs = mock_post.call_args_list[0]
    assert first_args[0] == "https://archon-enduser.vercel.app/api/telegram"
    proxy_json = first_kwargs.get("json", {})
    assert proxy_json.get("bot_token") == "fake_token"
    assert "voice_base64" in proxy_json
    assert proxy_json.get("caption") == "🎙️ Voice Test"

    # Second attempt falls back to Direct sendVoice
    second_args, second_kwargs = mock_post.call_args_list[1]
    assert second_args[0] == "https://api.telegram.org/botfake_token/sendVoice"
    assert "voice" in second_kwargs.get("files", {})


@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.TelegramService._get_config_async")
@patch("httpx.AsyncClient.post")
async def test_telegram_send_voice_proxy_http_status_error_falls_back_to_direct(mock_post, mock_get_config):
    """If Vercel Proxy returns HTTP 500/413 (raising HTTPStatusError), send_voice must still fall back to Direct."""
    import httpx

    mock_get_config.return_value = NotificationConfig.model_validate({
        "TELEGRAM_TOKEN": "fake_token",
        "TELEGRAM_TO": "fake_chat",
        "TELEGRAM_PROXY_URL": "https://archon-enduser.vercel.app/api/telegram",
        "TELEGRAM_RETRIES": 1,
    })

    mock_proxy_err_resp = MagicMock()
    mock_proxy_err_resp.status_code = 500
    mock_proxy_err_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Internal Server Error",
        request=httpx.Request("POST", "https://archon-enduser.vercel.app/api/telegram"),
        response=httpx.Response(500),
    )

    mock_direct_ok_resp = MagicMock()
    mock_direct_ok_resp.status_code = 200
    mock_direct_ok_resp.raise_for_status = MagicMock()

    mock_post.side_effect = [mock_proxy_err_resp, mock_direct_ok_resp]

    success = await telegram_service.send_voice(b"RIFF_WAV", caption="Fallback on HTTP 500")
    assert success is True
    assert mock_post.call_count == 2
    assert mock_post.call_args_list[0].args[0] == "https://archon-enduser.vercel.app/api/telegram"
    assert mock_post.call_args_list[1].args[0] == "https://api.telegram.org/botfake_token/sendVoice"

