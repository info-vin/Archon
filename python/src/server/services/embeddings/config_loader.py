"""
Configuration loader for embedding services.
"""

import os


# Deprecated functions - kept for backward compatibility
async def get_openai_api_key() -> str | None:
    """
    DEPRECATED: Use os.getenv("OPENAI_API_KEY") directly.
    API key is loaded into environment at startup.
    """
    return os.getenv("OPENAI_API_KEY")
