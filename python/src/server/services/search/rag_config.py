

def get_setting(key: str, default: str = "false") -> str:
    """Get a setting from credential service (SSOT)."""
    try:
        from src.server.services.settings_service import SettingsService
        from src.server.utils import get_supabase_client

        settings_service = SettingsService(get_supabase_client())
        all_settings = settings_service.get_all_settings()
        if key in all_settings:
            return str(all_settings[key])
        return default
    except Exception:
        return default


def get_bool_setting(key: str, default: bool = False) -> bool:
    """Get a boolean setting from credential service."""
    value = get_setting(key, "false" if not default else "true")
    return value.lower() in ("true", "1", "yes", "on")
