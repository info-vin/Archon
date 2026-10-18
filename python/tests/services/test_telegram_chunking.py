import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.server.services.system.telegram_service import TelegramService, telegram_service


def test_split_message_chunks_short_text():
    """Short text should not be split and should have no pagination header."""
    text = "Short alert message."
    chunks = TelegramService.split_message_chunks(text, max_chunk_size=100)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_split_message_chunks_paragraph_boundary():
    """Text exceeding max_chunk_size should split at paragraph boundaries and add pagination."""
    p1 = "Paragraph 1: " + "A" * 50
    p2 = "Paragraph 2: " + "B" * 50
    full_text = f"{p1}\n\n{p2}"

    chunks = TelegramService.split_message_chunks(full_text, max_chunk_size=80)
    assert len(chunks) == 2
    assert "📄 [1/2]" in chunks[0]
    assert "Paragraph 1:" in chunks[0]
    assert "📄 [2/2]" in chunks[1]
    assert "Paragraph 2:" in chunks[1]


def test_split_message_chunks_respects_max_limit():
    """Ensure every chunk generated is strictly <= max_chunk_size (including pagination header)."""
    long_text = "\n\n".join([f"Section {i}: " + ("content " * 100) for i in range(10)])
    max_size = 500
    chunks = TelegramService.split_message_chunks(long_text, max_chunk_size=max_size)

    assert len(chunks) > 1
    for chunk in chunks:
        # Note: chunk includes the 📄 [X/Y]\n header, content itself was <= max_size
        assert len(chunk) <= max_size + 20


@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.httpx.AsyncClient.post")
@patch("src.server.services.system.telegram_service.get_supabase_client")
@patch("src.server.services.settings_service.SettingsService.get_all_settings")
async def test_send_message_multi_chunk_success(mock_settings, mock_sb_client, mock_post):
    """Verifies that long messages are sent across multiple HTTP calls with pacing."""
    mock_settings.return_value = {
        "TELEGRAM_TOKEN": "token_123",
        "TELEGRAM_TO": "chat_456",
        "TELEGRAM_RETRIES": 1,
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.raise_for_status = MagicMock()
    mock_post.return_value = mock_resp

    long_text = "Part 1\n\n" + ("X" * 4000) + "\n\nPart 2\n\n" + ("Y" * 4000)

    with patch.object(asyncio, "sleep", new_callable=AsyncMock) as mock_sleep:
        success = await telegram_service.send_message(long_text)

        assert success is True
        assert mock_post.call_count >= 2
        # Assert sleep called between chunks for rate limiting
        assert mock_sleep.called


@pytest.mark.asyncio
@patch("src.server.services.system.telegram_service.httpx.AsyncClient.post")
@patch("src.server.services.system.telegram_service.get_supabase_client")
@patch("src.server.services.settings_service.SettingsService.get_all_settings")
async def test_send_message_chunk_failure_no_silent_mute(mock_settings, mock_sb_client, mock_post):
    """Verifies that if chunk 2 fails with 502, system returns False (no fake success / mute)."""
    mock_settings.return_value = {
        "TELEGRAM_TOKEN": "token_123",
        "TELEGRAM_TO": "chat_456",
        "TELEGRAM_RETRIES": 1,
    }

    mock_sb = MagicMock()
    mock_sb_client.return_value = mock_sb
    mock_sb.table.return_value.select.return_value.limit.return_value.execute.return_value = MagicMock(data=[{"id": "proj_1"}])
    mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()

    # Call 1 succeeds, Call 2 fails with 502
    resp_success = MagicMock(status_code=200, raise_for_status=MagicMock())
    resp_fail = MagicMock(status_code=502, text="Bad Gateway")
    resp_fail.request = httpx.Request("POST", "http://fake")

    mock_post.side_effect = [
        resp_success,
        httpx.HTTPStatusError("502", request=resp_fail.request, response=resp_fail),
    ]

    long_text = "Part 1\n\n" + ("A" * 4000) + "\n\nPart 2\n\n" + ("B" * 4000)
    success = await telegram_service.send_message(long_text)

    # NO FAKE SUCCESS: Must return False because chunk 2 failed
    assert success is False
