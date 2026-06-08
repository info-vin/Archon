import os
from typing import Any


async def check_credentials_exist(manager, keys: list[str]) -> dict[str, dict[str, Any]]:
    """
    Check if a list of credentials exist and have a value.
    Returns a dictionary with the status for each key.
    """
    if not manager._cache_initialized:
        await manager.load_all_credentials()

    statuses = {}
    for key in keys:
        value = manager._cache.get(key)
        has_value = False
        if value:
            if isinstance(value, dict) and value.get("is_encrypted"):
                if value.get("encrypted_value"):
                    has_value = True
            elif isinstance(value, str) and value:
                has_value = True

        # Step 2: Environment variable fallback (Physical Hardening)
        if not has_value:
            env_value = os.getenv(key) or os.getenv(key.upper())
            if not env_value and key == "GOOGLE_API_KEY":
                env_value = os.getenv("GEMINI_API_KEY")
            if env_value and env_value.strip():
                has_value = True

        statuses[key] = {"key": key, "has_value": has_value}

    return statuses
