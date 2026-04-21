"""
Model SSOT (Single Source of Truth) for Archon.
Physically aligns system-wide model identifiers with Google GenAI SDK requirements.
(Updated: 2026-04-21 based on Official Deprecation Docs)
Models optimized for Free Tier compatibility.
"""

SYSTEM_MODELS = {
    # Gemini 3.1 Flash-Lite: Best Free Tier model (15 RPM / 1000 RPD)
    "DEFAULT_TEXT": "models/gemini-3.1-flash-lite-preview",
    
    # Gemini 2.5 Pro: Last reasoning model with Free Tier (Deprecates June 17, 2026)
    "DEFAULT_PRO": "models/gemini-2.5-pro",
    
    # Image Models (Requires Billing for API, MarketingService uses internal fallback)
    "IMAGE_GEN": "models/gemini-2.5-flash-image",
    
    # Legacy Alignment (Kept per User Request - Deprecates July 2026)
    "EMBEDDING": "models/gemini-embedding-001"
}

def get_model_path(key: str, default: str = "DEFAULT_TEXT") -> str:
    """Returns the full physical path (e.g. models/...) for a given model key."""
    return SYSTEM_MODELS.get(key, SYSTEM_MODELS.get(default))
