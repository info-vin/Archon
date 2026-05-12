from ...config.logfire_config import get_logger

logger = get_logger(__name__)


async def get_embedding_model(provider: str | None = None) -> str:
    """Get the configured embedding model based on the provider."""
    # Late import to ensure physical identity with test patches
    from ..llm_provider_service import credential_service, get_cached_settings, is_valid_provider, set_cached_settings

    try:
        if provider:
            provider_name = provider
            cache_key = "rag_strategy_settings"
            rag_settings = get_cached_settings(cache_key)
            if rag_settings is None:
                rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
                if isinstance(rag_settings, dict):
                    set_cached_settings(cache_key, rag_settings)
            custom_model = rag_settings.get("EMBEDDING_MODEL", "")
        else:
            cache_key = "provider_config_embedding"
            provider_config = get_cached_settings(cache_key)
            if provider_config is None:
                provider_config = await credential_service.get_active_provider("embedding")
                if isinstance(provider_config, dict):
                    set_cached_settings(cache_key, provider_config)
            provider_name = provider_config["provider"]
            custom_model = provider_config["embedding_model"]

        if not is_valid_provider(provider_name):
            provider_name = "openai"

        if custom_model and len(str(custom_model).strip()) > 0:
            m = str(custom_model).strip()
            if len(m) <= 100 and not any(char in m for char in ["\n", "\r", "\t", "\0"]):
                return m

        raise ValueError(f"Embedding model is not configured for provider: {provider_name}")
    except Exception as e:
        logger.error(f"Error getting embedding model: {e}")
        raise


def is_openai_embedding_model(model: str) -> bool:
    if not model:
        return False
    model_lower = model.strip().lower()
    base_models = {"text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"}
    if model_lower in base_models:
        return True
    for separator in ("/", ":"):
        if separator in model_lower:
            candidate = model_lower.split(separator)[-1]
            if candidate in base_models:
                return True
    return any(base in model_lower for base in base_models)


def is_google_embedding_model(model: str) -> bool:
    if not model:
        return False
    patterns = [
        "text-embedding-004",
        "text-embedding-001",
        "text-embedding-005",
        "text-multilingual-embedding-002",
        "gemini-embedding-001",
        "multimodalembedding@001",
    ]
    return any(p in model.lower() for p in patterns)


def is_valid_embedding_model_for_provider(model: str, provider: str) -> bool:
    if not model or not provider:
        return False
    p_lower = provider.lower()
    if p_lower == "openai":
        return is_openai_embedding_model(model)
    if p_lower == "google":
        return is_google_embedding_model(model)
    if p_lower in ["openrouter", "anthropic", "grok"]:
        return is_openai_embedding_model(model) or is_google_embedding_model(model)
    if p_lower == "ollama":
        patterns = ["nomic-embed", "all-minilm", "mxbai-embed", "embed"]
        return any(p in model.lower() for p in patterns)
    return is_openai_embedding_model(model)


def get_supported_embedding_models(provider: str) -> list[str]:
    if not provider:
        return []
    p_lower = provider.lower()
    openai_models = ["text-embedding-ada-002", "text-embedding-3-small", "text-embedding-3-large"]
    google_models = [
        "text-embedding-004",
        "text-embedding-001",
        "text-embedding-005",
        "text-multilingual-embedding-002",
        "gemini-embedding-001",
        "multimodalembedding@001",
    ]
    if p_lower == "openai":
        return openai_models
    if p_lower == "google":
        return google_models
    if p_lower in ["openrouter", "anthropic", "grok"]:
        return openai_models + google_models
    if p_lower == "ollama":
        return ["nomic-embed-text", "all-minilm", "mxbai-embed-large"]
    return openai_models


def is_reasoning_model(model_name: str) -> bool:
    if not model_name:
        return False
    m = model_name.lower()
    prefixes = ("gpt-5", "o1", "o3", "o4", "grok", "deepseek-r", "deepseek-reasoner", "deepseek-chat-r")
    if m.startswith(prefixes):
        return True
    if "/" in m:
        parts = m.split("/")
        known = {"openai", "openrouter", "x-ai", "deepseek", "anthropic"}
        filtered = [p for p in parts if p not in known]
        if filtered and filtered[-1].startswith(prefixes):
            return True
    return False


def requires_max_completion_tokens(model_name: str) -> bool:
    return is_reasoning_model(model_name)


def prepare_chat_completion_params(model: str, params: dict) -> dict:
    if not model or not params:
        return params
    updated_params = params.copy()
    if is_reasoning_model(model):
        if "max_tokens" in updated_params:
            updated_params["max_completion_tokens"] = updated_params.pop("max_tokens")
        if "temperature" in updated_params:
            updated_params.pop("temperature")
    return updated_params
