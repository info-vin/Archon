import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.scheduler.jobs.task_dispatcher import run_task_dispatcher
from src.server.services.system.telegram_service import telegram_service


@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.httpx.AsyncClient.post")
@patch("src.server.services.system.telegram_service.get_supabase_client")
@patch("src.server.services.settings_service.SettingsService.get_all_settings")
async def test_telegram_persistence_queue(mock_settings, mock_sb_client, mock_post):
    import httpx

    mock_settings.return_value = {
        "TELEGRAM_TOKEN": "fake_token",
        "TELEGRAM_TO": "fake_chat",
        "TELEGRAM_RETRIES": 1
    }

    mock_response = MagicMock()
    mock_response.status_code = 502
    mock_response.text = "Bad Gateway"
    mock_response.request = httpx.Request("POST", "http://fake")
    mock_post.side_effect = httpx.HTTPStatusError("Mocked 502", request=mock_response.request, response=mock_response)

    mock_sb = MagicMock()
    mock_sb_client.return_value = mock_sb
    mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "proj_123"}])
    mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()

    # Send message with specific parse_mode to test serialization
    result = await telegram_service.send_message("Test Real Message", parse_mode="HTML")
    assert result is False

    import asyncio
    await asyncio.sleep(0.5)

    tables_called = [call.args[0] for call in mock_sb.table.call_args_list]
    assert "archon_tasks" in tables_called

    # Verify JSON serialization in the insert call
    insert_calls = mock_sb.table.return_value.insert.call_args_list
    assert len(insert_calls) > 0
    insert_data = insert_calls[1].args[0]

    print("INSERT DATA:", insert_data)
    assert insert_data["title"] == "[System] Pending Telegram Alert"

    # This must be a JSON string with text and parse_mode
    parsed_desc = json.loads(insert_data["description"])
    assert parsed_desc["text"] == "Test Real Message"
    assert parsed_desc["parse_mode"] == "HTML"


@pytest.mark.asyncio
@patch("src.server.services.scheduler.jobs.task_dispatcher.get_supabase_client")
async def test_task_dispatcher_flush(mock_sb_client):
    mock_sb = MagicMock()
    mock_repo = MagicMock()
    mock_sb_client.return_value = mock_sb

    with patch("src.server.repositories.base_repository.BaseRepository") as mock_base_repo_class:
        mock_base_repo_class.return_value = mock_repo

        call_count = 0
        def mock_exec(query, err):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Return the JSON serialized format
                fake_desc = json.dumps({"text": "Queued Message", "parse_mode": "HTML"})
                return True, {"data": [{"id": "task_123", "title": "Queued", "description": fake_desc}]}
            raise Exception("Stop here")
        mock_repo.execute_query = mock_exec

        with patch("src.server.services.system.telegram_service.TelegramService.send_message", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = True
            try:
                await run_task_dispatcher()
            except Exception:
                pass

            # Should correctly deserialize and pass parse_mode
            mock_send.assert_called_once_with("Queued Message", parse_mode="HTML", is_retry=True)

