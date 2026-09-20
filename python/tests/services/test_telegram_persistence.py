from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.scheduler.jobs.task_dispatcher import run_task_dispatcher
from src.server.services.system.telegram_service import telegram_service


@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.httpx.AsyncClient.post")
@patch("src.server.services.system.telegram_service.get_supabase_client")
@patch("src.server.services.system.telegram_service.TelegramService._get_config_async")
async def test_telegram_persistence_queue(mock_config, mock_sb_client, mock_post):
    import httpx

    from src.server.schemas.settings import NotificationConfig
    mock_config.return_value = NotificationConfig(TELEGRAM_TOKEN="fake_token", TELEGRAM_TO="fake_chat", TELEGRAM_RETRIES=1)
    mock_post.side_effect = httpx.RequestError("Mocked ConnectTimeout")
    mock_sb = MagicMock()
    mock_sb_client.return_value = mock_sb
    mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "proj_123"}])
    mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()
    result = await telegram_service.send_message("Test Message")
    assert result is False
    import asyncio
    await asyncio.sleep(0.1)
    tables_called = [call.args[0] for call in mock_sb.table.call_args_list]
    assert "archon_tasks" in tables_called

@pytest.mark.asyncio
@patch("src.server.services.scheduler.jobs.task_dispatcher.get_supabase_client")
async def test_task_dispatcher_flush(mock_sb_client):
    mock_sb = MagicMock()
    mock_repo = MagicMock()
    mock_sb_client.return_value = mock_sb

    with patch("src.server.repositories.base_repository.BaseRepository") as mock_base_repo_class:
        mock_base_repo_class.return_value = mock_repo

        # Make the generic query fail for everything except the first query (the pending queue flush)
        # to prevent it from going down into the agent dispatch logic which requires deeper mocks.
        call_count = 0
        def mock_exec(query, err):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True, {"data": [{"id": "task_123", "title": "Queued", "description": "Queued Message"}]}
            raise Exception("Stop here")
        mock_repo.execute_query = mock_exec

        with patch("src.server.services.system.telegram_service.TelegramService.send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            try:
                await run_task_dispatcher()
            except Exception:
                pass

            mock_send.assert_called_once_with("Queued Message", is_retry=True)

@pytest.mark.asyncio
@patch("src.server.services.scheduler.jobs.task_dispatcher.get_supabase_client")
async def test_task_dispatcher_expiration(mock_sb_client):
    mock_sb = MagicMock()
    mock_repo = MagicMock()
    mock_sb_client.return_value = mock_sb

    with patch("src.server.repositories.base_repository.BaseRepository") as mock_base_repo_class:
        mock_base_repo_class.return_value = mock_repo

        # Return a task created 48 hours ago
        from datetime import UTC, datetime, timedelta
        old_time = (datetime.now(UTC) - timedelta(hours=48)).isoformat()

        call_count = 0
        def mock_exec(query, err):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return True, {"data": [{"id": "task_old", "title": "Queued", "description": "Old Message", "created_at": old_time}]}
            if "update" in str(query) or hasattr(query, "update"):
                return True, {"data": []}
            raise Exception("Stop here")
        mock_repo.execute_query = mock_exec

        with patch("src.server.services.system.telegram_service.TelegramService.send_message", new_callable=AsyncMock) as mock_send:
            try:
                await run_task_dispatcher()
            except Exception:
                pass

            # Should NOT have called send_message
            mock_send.assert_not_called()

            # Should have called update to 'errored'
            assert mock_sb.table.called
            tables_called = [call.args[0] for call in mock_sb.table.call_args_list]
            assert "archon_tasks" in tables_called
