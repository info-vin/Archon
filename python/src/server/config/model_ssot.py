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
    "DEFAULT_PRO": "models/gemini-3.1-flash-lite",

    # Image Models (Requires Billing for API, MarketingService uses internal fallback)
    "IMAGE_GEN": "models/gemini-3.1-flash-image-preview",

    # TTS Model
    "TTS_MODEL": "models/gemini-3.1-flash-tts-preview",

    # Legacy Alignment (Kept per User Request - Deprecates July 2026)
    "EMBEDDING": "models/gemini-embedding-001"
}

def get_model_path(key: str, default: str = "DEFAULT_TEXT") -> str:
    """Returns the full physical path (e.g. models/...) for a given model key."""
    # Logic: Fallback to dictionary indexing to satisfy MyPy's str return guarantee
    path = SYSTEM_MODELS.get(key) or SYSTEM_MODELS[default]
    return str(path)
