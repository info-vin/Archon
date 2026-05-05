from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.text_to_speech_service import text_to_speech_service


@pytest.fixture
def mock_genai_client():
    with patch("src.server.services.text_to_speech_service.genai.Client") as mock:
        client_instance = mock.return_value

        # Mocking GenerateContentResponse
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_part = MagicMock()
        mock_part.inline_data = MagicMock()
        mock_part.inline_data.mime_type = "audio/wav"
        mock_part.inline_data.data = b"fake-audio-data"
        mock_candidate.content.parts = [mock_part]

        mock_response.candidates = [mock_candidate]
        client_instance.aio.models.generate_content = AsyncMock(return_value=mock_response)
        yield client_instance

@pytest.fixture
def mock_credential_service():
    with patch("src.server.services.text_to_speech_service.credential_service") as mock:
        mock.get_credential = AsyncMock(return_value="fake-api-key")
        yield mock

@pytest.mark.asyncio
async def test_generate_audio_success(mock_genai_client, mock_credential_service):
    success, data = await text_to_speech_service.generate_audio("Hello world")
    assert success is True
    # Verify the audio is wrapped in a valid WAV container
    assert data.startswith(b"RIFF")
    assert b"WAVEfmt" in data
    assert b"fake-audio-data" in data
    mock_genai_client.aio.models.generate_content.assert_called_once()

@pytest.mark.asyncio
async def test_generate_audio_missing_key():
    with patch("src.server.services.text_to_speech_service.credential_service.get_credential", new_callable=AsyncMock) as mock_creds:
        mock_creds.return_value = None
        success, data = await text_to_speech_service.generate_audio("Hello world")
        assert success is False
        assert "API Key" in data

@pytest.mark.asyncio
async def test_generate_audio_retry_exhausted(mock_credential_service):
    with patch("src.server.services.text_to_speech_service.genai.Client") as mock_client_class:
        mock_client = mock_client_class.return_value
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("429 Rate Limit Exceeded"))

        with pytest.raises(Exception) as excinfo:
            await text_to_speech_service.generate_audio("Test retry")

        assert "429 Rate Limit Exceeded" in str(excinfo.value)
        # Should have been called 3 times total (1 initial + 2 retries)
        assert mock_client.aio.models.generate_content.call_count == 3
