import pytest
from unittest.mock import patch, AsyncMock
from src.server.services.system.telegram_service import telegram_service
from src.server.schemas.settings import NotificationConfig

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
    
    # Setup mock response
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = AsyncMock()
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
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = AsyncMock()
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
