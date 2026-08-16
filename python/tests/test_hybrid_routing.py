from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.credential_service import credential_service
from src.server.services.credentials import provider_configs
from src.server.services.llm.clients import get_llm_client


def dummy_retry_decorator(*args, **kwargs):
    def decorator(func):
        return func
    return decorator

@pytest.fixture(autouse=True)
def mock_retry():
    with patch("src.server.utils.retry_utils.retry_with_backoff", dummy_retry_decorator):
        yield

@pytest.fixture(autouse=True)
def reset_active_tier():
    credential_service.set_active_tier(1)
    yield
    credential_service.set_active_tier(1)

@pytest.fixture
def mock_provider_config():
    return {
        "provider": "google",
        "api_key": "test-key",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "chat_model": "gemini-3.1-flash",
        "embedding_model": "text-embedding-004",
    }

@pytest.mark.asyncio
@patch("openai.AsyncOpenAI")
async def test_simple_offline_query_routes_to_tier3(mock_openai, mock_provider_config):
    """Test that a simple offline-compatible query routes to Tier 3 (Ollama) when available."""
    def mock_get_setting(key, default=None):
        if key == "ollama_discovered_models":
            return '{"chat_models": [{"name": "llama3:8b"}]}'
        elif key == "offline_allowed_models":
            return '["llama3"]'
        elif key == "local_inference_latency_ms":
            return "100"
        return default

    # Mock Tier 3 Client (Ollama)
    mock_ollama_client = MagicMock()
    mock_ollama_client.close = AsyncMock()
    mock_ollama_client.aclose = AsyncMock()
    mock_ollama_response = MagicMock()
    mock_ollama_response.choices = [MagicMock(message=MagicMock(content="Local Ollama Response"))]
    mock_ollama_client.chat.completions.create = AsyncMock(return_value=mock_ollama_response)

    # First client setup is for Tier 3
    mock_openai.return_value = mock_ollama_client

    with patch.object(provider_configs, "get_active_provider", AsyncMock(return_value=mock_provider_config)), \
         patch.object(credential_service, "get_credential", AsyncMock(return_value="0")), \
         patch.object(credential_service, "set_active_tier") as mock_set_tier, \
         patch("src.server.services.settings_service.SettingsService.get_setting", side_effect=mock_get_setting):

        async with get_llm_client() as client:
            res = await client.chat.completions.create(messages=[{"role": "user", "content": "Hello, how are you today?"}])
            assert res.choices[0].message.content == "Local Ollama Response"
            mock_set_tier.assert_called_with(3)

@pytest.mark.asyncio
@patch("openai.AsyncOpenAI")
async def test_complex_online_query_routes_to_tier1(mock_openai, mock_provider_config):
    """Test that a query containing search/online keywords or with long length routes to Tier 1."""
    def mock_get_setting(key, default=None):
        if key == "ollama_discovered_models":
            return '{"chat_models": [{"name": "llama3:8b"}]}'
        elif key == "offline_allowed_models":
            return '["llama3"]'
        elif key == "local_inference_latency_ms":
            return "100"
        return default

    # Mock Tier 1 Client (Cloud)
    mock_cloud_client = MagicMock()
    mock_cloud_client.close = AsyncMock()
    mock_cloud_client.aclose = AsyncMock()
    mock_cloud_response = MagicMock()
    mock_cloud_response.choices = [MagicMock(message=MagicMock(content="Cloud Response"))]
    mock_cloud_client.chat.completions.create = AsyncMock(return_value=mock_cloud_response)

    mock_openai.return_value = mock_cloud_client

    with patch.object(provider_configs, "get_active_provider", AsyncMock(return_value=mock_provider_config)), \
         patch.object(credential_service, "get_credential", AsyncMock(return_value="0")), \
         patch.object(credential_service, "set_active_tier") as mock_set_tier, \
         patch("src.server.services.settings_service.SettingsService.get_setting", side_effect=mock_get_setting):

        async with get_llm_client() as client:
            # Query containing "search" (online keyword)
            res = await client.chat.completions.create(messages=[{"role": "user", "content": "search for the latest python updates"}])
            assert res.choices[0].message.content == "Cloud Response"
            mock_set_tier.assert_called_with(1)

@pytest.mark.asyncio
@patch("openai.AsyncOpenAI")
async def test_ollama_unavailable_routes_to_tier1(mock_openai, mock_provider_config):
    """Test that a simple query routes to Tier 1 when Ollama is marked as unavailable."""
    def mock_get_setting(key, default=None):
        if key == "ollama_discovered_models":
            return '{"chat_models": []}'
        elif key == "offline_allowed_models":
            return '["llama3"]'
        elif key == "local_inference_latency_ms":
            return "100"
        return default

    # Mock Tier 1 Client (Cloud)
    mock_cloud_client = MagicMock()
    mock_cloud_client.close = AsyncMock()
    mock_cloud_client.aclose = AsyncMock()
    mock_cloud_response = MagicMock()
    mock_cloud_response.choices = [MagicMock(message=MagicMock(content="Cloud Response"))]
    mock_cloud_client.chat.completions.create = AsyncMock(return_value=mock_cloud_response)

    mock_openai.return_value = mock_cloud_client

    with patch.object(provider_configs, "get_active_provider", AsyncMock(return_value=mock_provider_config)), \
         patch.object(credential_service, "get_credential", AsyncMock(return_value="0")), \
         patch.object(credential_service, "set_active_tier") as mock_set_tier, \
         patch("src.server.services.settings_service.SettingsService.get_setting", side_effect=mock_get_setting):

        async with get_llm_client() as client:
            res = await client.chat.completions.create(messages=[{"role": "user", "content": "Hello"}])
            assert res.choices[0].message.content == "Cloud Response"
            mock_set_tier.assert_called_with(1)
