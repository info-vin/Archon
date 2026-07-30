from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import openai
import pytest

from src.server.services.credential_service import credential_service
from src.server.services.credentials import provider_configs
from src.server.services.llm.clients import get_llm_client


# Pass-through retry decorator to eliminate exponential backoff delays in tests
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
async def test_fallback_self_healing_on_success(mock_openai, mock_provider_config):
    """Test that active tier is set to 1 and self-healed when Tier 1 call succeeds."""
    mock_client = MagicMock()
    mock_client.close = AsyncMock()
    mock_client.aclose = AsyncMock()
    mock_openai.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Hello World"))]
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

    with patch.object(provider_configs, "get_active_provider", AsyncMock(return_value=mock_provider_config)), \
         patch.object(credential_service, "get_credential", AsyncMock(return_value="0")), \
         patch.object(credential_service, "set_active_tier") as mock_set_tier:

        async with get_llm_client() as client:
            res = await client.chat.completions.create(messages=[{"role": "user", "content": "test"}])
            assert res.choices[0].message.content == "Hello World"
            mock_set_tier.assert_called_with(1)

@pytest.mark.asyncio
@patch("openai.AsyncOpenAI")
async def test_fallback_to_tier2_huggingface_on_rate_limit(mock_openai, mock_provider_config):
    """Test that a 429 RateLimitError triggers Tier 2 fallback to Hugging Face."""
    # Mock Tier 1 Client (raises 429)
    mock_tier1_client = MagicMock()
    mock_tier1_client.close = AsyncMock()
    mock_tier1_client.aclose = AsyncMock()
    response = httpx.Response(429, request=httpx.Request("POST", "https://api.openai.com/v1"))
    mock_tier1_client.chat.completions.create = AsyncMock(side_effect=openai.RateLimitError("Rate Limit Exceeded", response=response, body=None))

    # Mock Tier 2 Client (succeeds)
    mock_hf_client = MagicMock()
    mock_hf_client.close = AsyncMock()
    mock_hf_client.aclose = AsyncMock()
    mock_hf_response = MagicMock()
    mock_hf_response.choices = [MagicMock(message=MagicMock(content="HF Response"))]
    mock_hf_client.chat.completions.create = AsyncMock(return_value=mock_hf_response)

    # Configure sequence of instantiations
    mock_openai.side_effect = [mock_tier1_client, mock_hf_client]

    mock_creds_dict = {
        "forced_fallback_tier": "0",
        "HF_TOKEN": "test-hf-token"
    }

    with patch.object(provider_configs, "get_active_provider", AsyncMock(return_value=mock_provider_config)), \
         patch.object(credential_service, "get_credential", AsyncMock(side_effect=lambda key, default=None: mock_creds_dict.get(key, ""))), \
         patch.object(credential_service, "set_active_tier") as mock_set_tier:

        async with get_llm_client() as client:
            res = await client.chat.completions.create(messages=[{"role": "user", "content": "test"}])
            assert res.choices[0].message.content == "HF Response"
            mock_set_tier.assert_any_call(2)

@pytest.mark.asyncio
@patch("openai.AsyncOpenAI")
async def test_fallback_to_tier3_ollama_on_connection_error(mock_openai, mock_provider_config):
    """Test that a connection error bypasses Tier 2 and falls back directly to Ollama (Tier 3)."""
    # Mock Tier 1 Client (raises ConnectionError)
    mock_tier1_client = MagicMock()
    mock_tier1_client.close = AsyncMock()
    mock_tier1_client.aclose = AsyncMock()
    mock_tier1_client.chat.completions.create = AsyncMock(side_effect=openai.APIConnectionError(request=httpx.Request("POST", "https://api.openai.com/v1")))

    # Mock Tier 3 Client (succeeds)
    mock_ollama_client = MagicMock()
    mock_ollama_client.close = AsyncMock()
    mock_ollama_client.aclose = AsyncMock()
    mock_ollama_response = MagicMock()
    mock_ollama_response.choices = [MagicMock(message=MagicMock(content="Ollama Response"))]
    mock_ollama_client.chat.completions.create = AsyncMock(return_value=mock_ollama_response)

    # Configure sequence of instantiations
    mock_openai.side_effect = [mock_tier1_client, mock_ollama_client]

    mock_creds_dict = {
        "forced_fallback_tier": "0",
        "HF_TOKEN": "test-hf-token"
    }

    with patch.object(provider_configs, "get_active_provider", AsyncMock(return_value=mock_provider_config)), \
         patch.object(credential_service, "get_credential", AsyncMock(side_effect=lambda key, default=None: mock_creds_dict.get(key, ""))), \
         patch.object(credential_service, "set_active_tier") as mock_set_tier:

        async with get_llm_client() as client:
            res = await client.chat.completions.create(messages=[{"role": "user", "content": "test"}])
            assert res.choices[0].message.content == "Ollama Response"
            mock_set_tier.assert_any_call(3)

@pytest.mark.asyncio
@patch("openai.AsyncOpenAI")
async def test_human_override_forces_fallback_tier(mock_openai, mock_provider_config):
    """Test that forced_fallback_tier manually redirects routing."""
    # Mock Tier 1 Client (should not be called for completion)
    mock_tier1_client = MagicMock()
    mock_tier1_client.close = AsyncMock()
    mock_tier1_client.aclose = AsyncMock()

    # Mock Tier 3 Client (succeeds)
    mock_ollama_client = MagicMock()
    mock_ollama_client.close = AsyncMock()
    mock_ollama_client.aclose = AsyncMock()
    mock_ollama_response = MagicMock()
    mock_ollama_response.choices = [MagicMock(message=MagicMock(content="Forced Ollama Response"))]
    mock_ollama_client.chat.completions.create = AsyncMock(return_value=mock_ollama_response)

    # Configure sequence of instantiations
    mock_openai.side_effect = [mock_tier1_client, mock_ollama_client]

    mock_creds_dict = {
        "forced_fallback_tier": "3",
    }

    with patch.object(provider_configs, "get_active_provider", AsyncMock(return_value=mock_provider_config)), \
         patch.object(credential_service, "get_credential", AsyncMock(side_effect=lambda key, default=None: mock_creds_dict.get(key, ""))), \
         patch.object(credential_service, "set_active_tier") as mock_set_tier:

        async with get_llm_client() as client:
            res = await client.chat.completions.create(messages=[{"role": "user", "content": "test"}])
            assert res.choices[0].message.content == "Forced Ollama Response"
            mock_set_tier.assert_called_with(3)
            # Ensure Tier 1 was never called for completion
            mock_tier1_client.chat.completions.create.assert_not_called()
