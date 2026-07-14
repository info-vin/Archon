import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from src.server.services.system.telegram_service import TelegramService
from src.server.services.scheduler.jobs.business import analyze_token_usage

@pytest.mark.asyncio
async def test_telegram_service_send_message(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "fake_token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "fake_chat_id")
    
    service = TelegramService()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value.status_code = 200
        result = await service.send_message("Test message")
        
        assert result is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["text"] == "Test message"
        assert kwargs["json"]["chat_id"] == "fake_chat_id"

@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
@patch("src.server.services.scheduler.jobs.business.get_supabase_client")
async def test_analyze_token_usage_triggers_alert_when_exceeded(mock_get_supabase, mock_send_message):
    # Mock supabase client and response for 7-day cost > 0.05
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    # Setup mock response for daily and weekly queries
    # First execute is daily, second is weekly
    mock_execute_daily = MagicMock()
    mock_execute_daily.data = [{"input_tokens": 100, "output_tokens": 100, "cost_usd": 0.01}]
    
    mock_execute_weekly = MagicMock()
    # Total cost = 0.06 (> 0.05 threshold)
    mock_execute_weekly.data = [{"cost_usd": 0.06}]
    
    # We need to chain the supabase query builder mock
    mock_select = mock_supabase.table.return_value.select.return_value
    mock_select.gt.return_value.execute.side_effect = [mock_execute_daily, mock_execute_weekly]
    
    await analyze_token_usage()
    
    mock_send_message.assert_called_once()
    args, _ = mock_send_message.call_args
    assert "Weekly Budget Exceeded" in args[0]
    assert "$0.0600 USD" in args[0]

@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.telegram_service.send_message", new_callable=AsyncMock)
@patch("src.server.services.scheduler.jobs.business.get_supabase_client")
async def test_analyze_token_usage_no_alert_when_safe(mock_get_supabase, mock_send_message):
    # Mock supabase client and response for 7-day cost <= 0.05
    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase
    
    mock_execute_daily = MagicMock()
    mock_execute_daily.data = [{"input_tokens": 100, "output_tokens": 100, "cost_usd": 0.01}]
    
    mock_execute_weekly = MagicMock()
    # Total cost = 0.04 (<= 0.05 threshold)
    mock_execute_weekly.data = [{"cost_usd": 0.04}]
    
    mock_select = mock_supabase.table.return_value.select.return_value
    mock_select.gt.return_value.execute.side_effect = [mock_execute_daily, mock_execute_weekly]
    
    await analyze_token_usage()
    
    mock_send_message.assert_not_called()
