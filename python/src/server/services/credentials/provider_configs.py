from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .manager import CredentialManager

from ...config.logfire_config import get_logger
from .models import ActiveProviderDTO, EmbeddingProviderConfigDTO

logger = get_logger(__name__)

SUPPORTED_PROVIDERS = {"openai", "google", "anthropic", "openrouter", "grok"} # 合法


async def get_active_provider(manager: "CredentialManager", service_type: str = "llm") -> ActiveProviderDTO:
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
        provider_val = all_settings.get(provider_key)

        if not provider_val:
            provider_raw = await manager.get_credential(provider_key, "google")
            provider = str(provider_raw).lower() if provider_raw else "google"
        else:
            provider = str(provider_val).lower()

        api_key = await _get_provider_api_key(manager, provider)
        base_url = _get_provider_base_url(provider, all_settings)

        chat_model_raw = all_settings.get("MODEL_CHOICE") or all_settings.get("MARKETING_MODEL") or ""
        chat_model = str(chat_model_raw) if not isinstance(chat_model_raw, dict) else ""

        embedding_model_raw = all_settings.get("EMBEDDING_MODEL", "")
        embedding_model = str(embedding_model_raw) if not isinstance(embedding_model_raw, dict) else ""

        return {
            "provider": provider,
            "api_key": api_key,
            "base_url": base_url,
            "chat_model": chat_model,
            "embedding_model": embedding_model,
        }

    except Exception as e:
        logger.error(f"Error getting active provider for {service_type}: {e}")
        provider_raw = await manager.get_credential("LLM_PROVIDER", "google")
        provider = str(provider_raw) if provider_raw else "google"
        openai_key = await manager.get_credential("OPENAI_API_KEY")
        return {
            "provider": provider,
            "api_key": str(openai_key) if openai_key else None,
            "base_url": None,
            "chat_model": "",
            "embedding_model": "",
        }


async def get_embedding_provider_configs(manager: "CredentialManager") -> list[EmbeddingProviderConfigDTO]:
    """
    Get the currently active primary and fallback embedding provider configurations.
    Designed for failover and separate from the main LLM provider logic.
    """
    configs: list[EmbeddingProviderConfigDTO] = []
    try:
        ai_settings = await manager.get_credentials_by_category("ai")
        marketing_settings = await manager.get_credentials_by_category("marketing")
        rag_settings = await manager.get_credentials_by_category("rag_strategy")

        all_settings = {**ai_settings, **marketing_settings, **rag_settings}

        provider_types = [
            {"type": "primary", "suffix": ""},
            {"type": "fallback", "suffix": "_FALLBACK"},
        ]

        for pt in provider_types:
            provider_key = f"EMBEDDING_PROVIDER{pt['suffix']}"
            model_key = f"EMBEDDING_MODEL{pt['suffix']}"
            api_key_override_key = f"EMBEDDING_API_KEY{pt['suffix']}"

            provider_val = all_settings.get(provider_key)
            if not provider_val:
                if pt["type"] == "primary":
                    provider_raw = all_settings.get("LLM_PROVIDER") or await manager.get_credential("LLM_PROVIDER", "google")
                    provider = str(provider_raw).lower() if provider_raw else "google"
                else:
                    continue
            else:
                provider = str(provider_val).lower()

            embedding_model_val = all_settings.get(model_key)
            embedding_model = str(embedding_model_val) if isinstance(embedding_model_val, str) else ""

            if not embedding_model and pt["type"] == "primary":
                fallback_val = all_settings.get("EMBEDDING_MODEL") or await manager.get_credential("EMBEDDING_MODEL", "")
                embedding_model = str(fallback_val) if fallback_val else ""

            if not embedding_model:
                if provider == "google":
                    embedding_model = "gemini-embedding-001"
                elif provider == "openai":
                    embedding_model = "text-embedding-3-small"
                else:
                    embedding_model = "default-embedding"

            api_key_raw = await manager.get_credential(api_key_override_key)
            api_key = str(api_key_raw) if api_key_raw else None

            if not api_key:
                api_key = await _get_provider_api_key(manager, provider)

            base_url = _get_provider_base_url(provider, all_settings)

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


async def _get_provider_api_key(manager: "CredentialManager", provider: str) -> str | None:
    """Get API key for a specific provider."""
    key_mapping = {
        "openai": "OPENAI_API_KEY",
        "google": "GEMINI_API_KEY", # Historically was GOOGLE_API_KEY, but providers_api used either. We'll check both if needed, but GEMINI_API_KEY is standard.
        "anthropic": "ANTHROPIC_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "grok": "XAI_API_KEY",
        "ollama": None,
    }

    # If GEMINI_API_KEY fails for google, fallback to GOOGLE_API_KEY
    if provider == "google":
        key = await manager.get_credential("GEMINI_API_KEY")
        if not key:
            key = await manager.get_credential("GOOGLE_API_KEY")
        return str(key) if key else None

    if provider == "grok":
        key = await manager.get_credential("GROK_API_KEY")
        if not key:
            key = await manager.get_credential("XAI_API_KEY")
        return str(key) if key else None

    key_name = key_mapping.get(provider)
    if key_name:
        key = await manager.get_credential(key_name)
        return str(key) if key else None
    return "ollama" if provider == "ollama" else None


def _get_provider_base_url(provider: str, rag_settings: dict[str, Any]) -> str | None:
    """Get base URL for provider."""
    if provider == "ollama":
        default_url = "http://localhost:11434/v1"  # 合法
        url_val = rag_settings.get("LLM_BASE_URL", default_url)
        return str(url_val) if isinstance(url_val, str) else default_url
    elif provider == "google":
        # The correct base URL for Google models endpoint (used in providers_api.py) is:
        # https://generativelanguage.googleapis.com/v1beta
        # liteLLM handles it differently, but for raw API tests we need this.
        return "https://generativelanguage.googleapis.com/v1beta"
    elif provider == "openai":
        return "https://api.openai.com/v1"
    elif provider == "anthropic":
        return "https://api.anthropic.com/v1"
    elif provider == "openrouter":
        return "https://openrouter.ai/api/v1"
    elif provider == "grok":
        return "https://api.x.ai/v1"
    return None


def _get_provider_auth_headers(provider: str, api_key: str) -> dict[str, str]:
    """Get authentication headers for provider."""
    if provider == "google":
        return {"x-goog-api-key": api_key}
    elif provider == "anthropic":
        return {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    else:
        return {"Authorization": f"Bearer {api_key}"}


async def set_active_provider(manager: "CredentialManager", provider: str, service_type: str = "llm") -> bool:
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
