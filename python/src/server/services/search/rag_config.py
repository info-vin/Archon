import os


def get_setting(key: str, default: str = "false") -> str:
    """Get a setting from the credential service or fall back to environment variable."""
    try:
        from ..credential_service import credential_service

        if hasattr(credential_service, "_cache") and credential_service._cache_initialized:
            cached_value = credential_service._cache.get(key)
            if isinstance(cached_value, dict) and cached_value.get("is_encrypted"):
                encrypted_value = cached_value.get("encrypted_value")
                if encrypted_value:
                    try:
                        from src.server.services.credentials.crypto_utils import CryptoUtils

                        return CryptoUtils.decrypt_value(encrypted_value)
                    except Exception:
                        pass
            elif cached_value:
                return str(cached_value)
        # Fallback to environment variable
        return os.getenv(key, default)
    except Exception:
        return os.getenv(key, default)


def get_bool_setting(key: str, default: bool = False) -> bool:
    """Get a boolean setting from credential service."""
    value = get_setting(key, "false" if not default else "true")
    return value.lower() in ("true", "1", "yes", "on")
