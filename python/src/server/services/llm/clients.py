import inspect
import uuid
from contextlib import asynccontextmanager
from typing import Any

import openai

from ...config.logfire_config import get_logger
from ...schemas.settings import NetworkConfig
from .base import MockLLMClient, UsageTrackingClient

logger = get_logger(__name__)


@asynccontextmanager
async def get_llm_client(
    provider: str | None = None,
    use_embedding_provider: bool = False,
    instance_type: str | None = None,
    base_url: str | None = None,
    user_id: str | None = None,
    request_id: str | None = None,
    api_key: str | None = None,
):
    """Create an async OpenAI-compatible client based on the configured provider."""
    # LATE IMPORT to ensure physical identity with test patches in Facade
    from ..credentials.provider_configs import _get_provider_api_key, _get_provider_base_url, get_active_provider
    from ..llm_provider_service import (
        credential_service,
        get_cached_settings,
        is_valid_provider,
        sanitize_for_log,
        set_cached_settings,
    )

    resolved_api_key = api_key
    client = None
    provider_name = provider

    try:
        if provider:
            provider_name = provider
            if not resolved_api_key:
                resolved_api_key = await _get_provider_api_key(credential_service, provider)
            cache_key = "rag_strategy_settings"
            rag_settings = get_cached_settings(cache_key)
            if rag_settings is None:
                rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
                if isinstance(rag_settings, dict):
                    set_cached_settings(cache_key, rag_settings)
            if provider != "ollama":
                base_url = _get_provider_base_url(provider, rag_settings)
            else:
                base_url = None
        else:
            service_type = "embedding" if use_embedding_provider else "llm"
            cache_key = f"provider_config_{service_type}"
            config = get_cached_settings(cache_key)
            if config is None:
                config = await get_active_provider(credential_service, service_type)
                if isinstance(config, dict):
                    set_cached_settings(cache_key, config)
            provider_name = config["provider"]
            if not resolved_api_key:
                resolved_api_key = config["api_key"]
            if provider_name != "ollama":
                base_url = config["base_url"]
            else:
                base_url = None

        if not is_valid_provider(provider_name):
            raise ValueError(f"Unsupported LLM provider: {provider_name}")

        if resolved_api_key:
            if len(resolved_api_key.strip()) == 0:
                resolved_api_key = None
            elif len(resolved_api_key) > 500:
                raise ValueError("API key length exceeds security limits")
            if resolved_api_key and any(char in resolved_api_key for char in ["\n", "\r", "\t", "\0"]):
                raise ValueError("API key contains invalid characters")

        if not resolved_api_key and provider_name in ["openai", "google", "anthropic", "grok", "openrouter"]: # 合法
            if provider_name == "openai":
                try:
                    url = await _get_optimal_ollama_instance("chat", False, base_url)
                    logger.info(f"OpenAI key missing, falling back to Ollama at {url}")
                    client = openai.AsyncOpenAI(api_key="ollama", base_url=url)
                    provider_name = "ollama"
                    base_url = url
                except Exception:
                    raise ValueError("OpenAI API key not found and Ollama fallback failed") from None
            else:
                from ...config.config import get_config
                if not get_config().is_testing:
                    raise ValueError(
                        f"CRITICAL: {provider_name.capitalize()} API key not found in environment or database. "
                        "MockClient fallback is disabled in non-testing environments."
                    )
                logger.warning(f"No API key found for {provider_name}. Using MockClient.")
                yield MockLLMClient(provider_name)
                return

        safe_p = sanitize_for_log(provider_name) if provider_name else "unknown"
        logger.info(f"Creating LLM client for provider: {safe_p}")

        if provider_name == "openai" and not client:
            client = openai.AsyncOpenAI(api_key=resolved_api_key)
        elif provider_name == "ollama":
            url = await _get_optimal_ollama_instance(instance_type, use_embedding_provider, base_url)
            client = openai.AsyncOpenAI(api_key="ollama", base_url=url)
        elif provider_name == "google":
            if not resolved_api_key:
                raise ValueError("Google API key not found")
            google_url = NetworkConfig().google_base_url
            client = openai.AsyncOpenAI(
                api_key=resolved_api_key,
                base_url=google_url,
                default_headers={"x-goog-api-key": resolved_api_key.strip()},
            )
        elif provider_name == "grok":
            if not resolved_api_key:
                raise ValueError("Grok API key not found - set GROK_API_KEY environment variable")
            client = openai.AsyncOpenAI(api_key=resolved_api_key, base_url=base_url or "https://api.x.ai/v1") # 合法
        elif provider_name == "openrouter":
            if not resolved_api_key:
                raise ValueError("OpenRouter API key not found")
            client = openai.AsyncOpenAI(
                api_key=resolved_api_key,
                base_url=base_url or NetworkConfig().openrouter_base_url,
                default_headers={
                    "HTTP-Referer": "https://github.com/info-vin/Archon", # 合法
                    "X-Title": "Archon AI",
                },
            )
        elif provider_name == "anthropic":
            # Anthropic uses a different SDK typically, but many proxies support OpenAI-compatible access
            if not resolved_api_key:
                raise ValueError("Anthropic API key not found")
            client = openai.AsyncOpenAI(
                api_key=resolved_api_key, base_url=base_url or NetworkConfig().anthropic_base_url
            )
        elif provider_name == "huggingface":
            if not resolved_api_key:
                from ..llm_provider_service import credential_service
                resolved_api_key = await credential_service.get_credential("HF_TOKEN")
            if not resolved_api_key:
                raise ValueError("Hugging Face API token (HF_TOKEN) not found")
            client = openai.AsyncOpenAI(
                api_key=resolved_api_key,
                base_url=base_url or NetworkConfig().hf_base_url
            )
        else:
            if not client:
                client = openai.AsyncOpenAI(api_key=resolved_api_key or "unused", base_url=base_url)

        if client and hasattr(client, "chat") and hasattr(client.chat, "completions"):
            yield UsageTrackingClient(client, user_id or "system", request_id or str(uuid.uuid4()), provider_name or "unknown")
        else:
            yield client

    finally:
        if client:
            close_method = getattr(client, "aclose", getattr(client, "close", None))
            if callable(close_method):
                if inspect.iscoroutinefunction(close_method):
                    await close_method()
                else:
                    res = close_method()
                    if inspect.isawaitable(res):
                        await res


async def create_embedding_client(config: dict[str, Any]) -> openai.AsyncOpenAI:
    p = config.get("provider")
    key = config.get("api_key")
    url = config.get("base_url")

    if not p:
        raise ValueError("Provider not specified in embedding configuration")

    if p == "openai":
        if not key:
            raise ValueError("OpenAI API key not found")
        return openai.AsyncOpenAI(api_key=key)
    if p == "ollama":
        return openai.AsyncOpenAI(api_key="ollama", base_url=url)
    if p == "google":
        if not key:
            raise ValueError("Google API key not found")
        return openai.AsyncOpenAI(
            api_key=key,
            base_url=url or NetworkConfig().google_base_url,
            default_headers={"x-goog-api-key": key.strip()},
        )

    if p != "ollama":
        raise ValueError(f"Unsupported embedding provider: {p}")

    return openai.AsyncOpenAI(api_key=key, base_url=url)


async def _get_optimal_ollama_instance(instance_type: str | None = None, use_embedding: bool = False, override: str | None = None) -> str:
    if override:
        if isinstance(override, str):
            if override.endswith("/v1"):
                return override
            return f"{override}/v1"
        return override

    from ..llm_provider_service import credential_service

    rag_data = await credential_service.get_credentials_by_category("rag_strategy")

    from ...schemas.settings import NetworkConfig
    from ...services.settings_service import SettingsService
    try:
        net_config = NetworkConfig.model_validate(SettingsService().get_all_settings())
        ollama_default = net_config.ollama_base_url
    except Exception:
        ollama_default = NetworkConfig().ollama_base_url

    # DEFENSIVE: Ensure we have a real dictionary (handles Mock objects in tests)
    if not isinstance(rag_data, dict):
        return f"{ollama_default}/v1" if not ollama_default.endswith("/v1") else ollama_default

    if use_embedding or instance_type == "embedding":
        embedding_url = rag_data.get("OLLAMA_EMBEDDING_URL")
        # DEFENSIVE: Ensure we have a real string
        if isinstance(embedding_url, str) and embedding_url:
            if embedding_url.endswith("/v1"):
                return embedding_url
            return f"{embedding_url}/v1"

    url = rag_data.get("LLM_BASE_URL", ollama_default)
    # DEFENSIVE: Ensure we have a real string
    if isinstance(url, str):
        if url.endswith("/v1"):
            return url
        return f"{url}/v1"
    return f"{ollama_default}/v1" if not ollama_default.endswith("/v1") else ollama_default
