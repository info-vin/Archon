"""
Model SSOT (Single Source of Truth) for Archon.
Physically aligns system-wide model identifiers with Google GenAI SDK requirements.
(Updated: 2026-04-21 based on Official Deprecation Docs)
Models optimized for Free Tier compatibility.
"""

SYSTEM_MODELS = {
    # Gemini 3.1 Flash-Lite: Best Free Tier model (15 RPM / 1000 RPD)
    "DEFAULT_TEXT": "models/gemini-3.1-flash-lite",
    # Gemini 3 Flash: Best Free Tier model for reasoning
    "DEFAULT_PRO": "models/gemini-3.5-flash-lite",
    # Image Models (Requires Billing for API, MarketingService uses internal fallback)
    "IMAGE_GEN": "models/gemini-3.1-flash-image-preview",
    # TTS Model
    "TTS_MODEL": "models/gemini-3.1-flash-tts-preview",
    # Legacy Alignment (Kept per User Request - Deprecates July 2026)
    "EMBEDDING": "models/gemini-embedding-001",
}

export_TARGET_MODELS = [
    {"key": "DEFAULT_TEXT", "agent": "General Text", "provider": "google"},
    {"key": "IMAGE_GEN", "agent": "Marketing (Imagen)", "provider": "google"},
    {"key": "DEFAULT_PRO", "agent": "Reasoning & Coding", "provider": "google"},
    {"key": "EMBEDDING", "agent": "Knowledge (Embedding)", "provider": "google"},
]

def get_target_models() -> list[dict]:
    """Returns the monitoring target models using current paths."""
    targets = []
    for t in export_TARGET_MODELS:
        targets.append({
            "id": get_model_path(t["key"]).replace("models/", ""),
            "agent": t["agent"],
            "provider": t["provider"]
        })
    return targets


def get_model_path(key: str, default: str = "DEFAULT_TEXT") -> str:
    """Returns the full physical path (e.g. models/...) for a given model key."""
    # Logic: Fallback to dictionary indexing to satisfy MyPy's str return guarantee
    path = SYSTEM_MODELS.get(key) or SYSTEM_MODELS[default]
    return str(path)

def get_active_fallback(key: str, available_models: list[str]) -> str:
    """
    Returns an active fallback model if the default one is not in available_models.
    Prioritizes Free Tier models (flash-lite).
    """
    default_model = SYSTEM_MODELS.get(key) or SYSTEM_MODELS["DEFAULT_TEXT"]
    default_name = default_model.replace("models/", "")

    if default_name in available_models:
        return default_model

    # Fallback logic: Find any available flash-lite model (Free Tier priority)
    for model in available_models:
        if "flash-lite" in model:
            return f"models/{model}"

    # Find any available flash model
    for model in available_models:
        if "flash" in model:
            return f"models/{model}"

    # Fallback to whatever is available
    if available_models:
        return f"models/{available_models[0]}"

    return default_model
