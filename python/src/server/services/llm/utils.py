import time
from typing import Any

from ...config.logfire_config import get_logger

logger = get_logger(__name__)

# SHARED STATE - Defined here to allow clean top-level imports in Facade
_settings_cache: dict[str, tuple[Any, float]] = {}
_cache_access_log: list[dict[str, Any]] = []
_CACHE_TTL_SECONDS = 300  # 5 minutes

def get_cached_settings(key: str) -> Any | None:
    """Get cached settings if not expired."""
    # DEFENSIVE: Ensure key is hashable
    safe_key = str(key) if isinstance(key, dict) else key

    if safe_key in _settings_cache:
        value, timestamp = _settings_cache[safe_key]
        if time.time() - timestamp < _CACHE_TTL_SECONDS:
            return value
        else:
            del _settings_cache[safe_key]
    return None

def set_cached_settings(key: str, value: Any) -> None:
    """Cache settings with current timestamp."""
    # DEFENSIVE: Ensure key is hashable
    safe_key = str(key) if isinstance(key, dict) else key
    _settings_cache[safe_key] = (value, time.time())

def is_valid_provider(provider_name: str | None) -> bool:
    """Check if a provider is supported and valid."""
    if not provider_name:
        return False
    if len(provider_name) > 100:
        return False
    # REMOVED "custom-unsupported" to allow test ValueError to trigger
    valid = ["openai", "ollama", "google", "openrouter", "anthropic", "grok", "mock"]
    return provider_name.lower() in valid

def sanitize_for_log(input_string: str) -> str:
    """Sanitize strings for logging to prevent injection attacks."""
    if not input_string:
        return ""
    return "".join(c if c.isalnum() or c in ['-', '_', '.'] else '_' for c in input_string)

def get_cache_security_report() -> dict[str, Any]:
    """Get detailed security report for cache monitoring."""
    current_time = time.time()
    report: dict[str, Any] = {
        "timestamp": current_time,
        "analysis_period_hours": 1,
        "security_events": [],
        "recommendations": []
    }
    recent_threshold = current_time - 3600
    security_events = [
        access for access in _cache_access_log
        if access.get("timestamp", 0) >= recent_threshold and access.get("security_event")
    ]
    report["security_events"] = security_events
    if len(security_events) > 10:
        report["recommendations"].append("High number of security events detected")
    return report
