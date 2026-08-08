"""
Configuration loader for embedding services.
"""



# Deprecated functions - kept for backward compatibility
async def get_openai_api_key() -> str | None:
    """
    DEPRECATED: Use get_config().openai_api_key directly.
    API key is loaded into environment at startup.
    """
    from ...config.config import get_config
    return get_config().openai_api_key
