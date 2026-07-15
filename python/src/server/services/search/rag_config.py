import os


def get_setting(key: str, default: str = "false") -> str:
    """Get a setting from credential service (deprecated, use RagConfig)."""
    try:
        from src.server.schemas.settings import RagConfig
        from src.server.services.settings_service import SettingsService
        from src.server.utils import get_supabase_client

        settings_service = SettingsService(get_supabase_client())
        config = RagConfig.model_validate(settings_service.get_all_settings())
        if key == "AGENTS_ENABLED":
            return str(config.agents_enabled)
        elif key == "USE_RERANKING":
            return str(config.use_reranking)
        return os.getenv(key, default)
    except Exception:
        return os.getenv(key, default)


def get_bool_setting(key: str, default: bool = False) -> bool:
    """Get a boolean setting from credential service."""
    value = get_setting(key, "false" if not default else "true")
    return value.lower() in ("true", "1", "yes", "on")
