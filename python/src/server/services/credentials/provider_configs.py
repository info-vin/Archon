import os
from typing import Any, cast

from ...config.logfire_config import get_logger

logger = get_logger(__name__)

async def get_active_provider(manager: Any, service_type: str = "llm") -> dict[str, Any]:
    """
    Get the currently active provider configuration.
    Searches across critical categories with deep fallback to OS environment.
    """
    try:
        ai_settings = await manager.get_credentials_by_category("ai")
        marketing_settings = await manager.get_credentials_by_category("marketing")
        rag_settings = await manager.get_credentials_by_category("rag_strategy")

        all_settings = {**ai_settings, **marketing_settings, **rag_settings}

        provider_key = "LLM_PROVIDER" if service_type == "llm" else "EMBEDDING_PROVIDER"
        provider = all_settings.get(provider_key)

        if not provider:
            provider = os.getenv(provider_key, "openai").lower()

        api_key = await _get_provider_api_key(manager, provider)
        base_url = _get_provider_base_url(provider, all_settings)

        chat_model = all_settings.get("MODEL_CHOICE") or all_settings.get("MARKETING_MODEL") or ""
        embedding_model = all_settings.get("EMBEDDING_MODEL", "")

        return {
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "chat_model": chat_model,
            "embedding_model": embedding_model,
        }

    except Exception as e:
        logger.error(f"Error getting active provider for {service_type}: {e}")
        provider = os.getenv("LLM_PROVIDER", "openai")
        return {
            "provider": provider,
            "api_key": os.getenv("OPENAI_API_KEY"),
            "base_url": None,
            "chat_model": "",
            "embedding_model": "",
        }

async def get_embedding_provider_configs(manager: Any) -> list[dict[str, Any]]:
    """
    Get the currently active primary and fallback embedding provider configurations.
    Designed for failover and separate from the main LLM provider logic.
    """
    configs = []
    try:
        rag_settings = await manager.get_credentials_by_category("rag_strategy")

        provider_types = [
            {"type": "primary", "suffix": ""},
            {"type": "fallback", "suffix": "_FALLBACK"},
        ]

        for pt in provider_types:
            provider_key = f"EMBEDDING_PROVIDER{pt['suffix']}"
            model_key = f"EMBEDDING_MODEL{pt['suffix']}"
            api_key_override_key = f"EMBEDDING_API_KEY{pt['suffix']}"

            provider = rag_settings.get(provider_key)
            if not provider:
                if pt["type"] == "primary":
                    provider = rag_settings.get("LLM_PROVIDER", "openai")
                else:
                    continue

            embedding_model = rag_settings.get(model_key)
            if not embedding_model and pt["type"] == "primary":
                embedding_model = rag_settings.get("EMBEDDING_MODEL")

            if not provider or not embedding_model:
                continue

            api_key = await manager.get_credential(api_key_override_key)
            if not api_key:
                api_key = await _get_provider_api_key(manager, provider)

            base_url = _get_provider_base_url(provider, rag_settings)

            if api_key:
                configs.append(
                    {
                        "provider": provider,
                        "api_key": api_key,
                        "base_url": base_url,
                        "embedding_model": embedding_model,
                    }
                )

        return configs

    except Exception as e:
        logger.error(f"Error getting embedding provider configs: {e}")
        return []

async def _get_provider_api_key(manager: Any, provider: str) -> str | None:
    """Get API key for a specific provider."""
    key_mapping = {
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "ollama": None,
    }

    key_name = key_mapping.get(provider)
    if key_name:
        return cast(str | None, await manager.get_credential(key_name))
    return "ollama" if provider == "ollama" else None

def _get_provider_base_url(provider: str, rag_settings: dict) -> str | None:
    """Get base URL for provider."""
    if provider == "ollama":
        return cast(str | None, rag_settings.get("LLM_BASE_URL", "http://localhost:11434/v1"))
    elif provider == "google":
        return "https://generativelanguage.googleapis.com/v1beta/openai/"
    return None

async def set_active_provider(manager: Any, provider: str, service_type: str = "llm") -> bool:
    """Set the active provider for a service type."""
    try:
        return bool(
            await manager.set_credential(
                "llm_provider",
                provider,
                category="rag_strategy",
                description=f"Active {service_type} provider",
            )
        )
    except Exception as e:
        logger.error(f"Error setting active provider {provider} for {service_type}: {e}")
        return False
