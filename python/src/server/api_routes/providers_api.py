"""
Provider status API endpoints for testing connectivity

Handles server-side provider connectivity testing without exposing API keys to frontend.
"""

from typing import cast

import httpx
from fastapi import APIRouter, HTTPException, Path

from ..config.logfire_config import get_logger
from ..services.credential_service import credential_service

# Provider validation - simplified inline version

logger = get_logger(__name__)
router = APIRouter(prefix="/api/providers", tags=["providers"])


async def test_openai_connection(api_key: str) -> bool:
    """Test OpenAI API connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return cast(bool, response.status_code == 200)
    except Exception as e:
        logger.warning(f"OpenAI connectivity test failed: {e}")
        return False


async def test_google_connection(api_key: str) -> bool:
    """Test Google AI API connectivity"""
    try:
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if api_key else "None"
        logger.info(f"Checking Google connectivity with key: {masked_key} (len={len(api_key)})")

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                headers={"x-goog-api-key": api_key} # Service handles stripping now
            )
            logger.info(f"Google API response: {response.status_code}")
            if response.status_code != 200:
                logger.warning(f"Google API Error Body: {response.text[:200]}")
            return cast(bool, response.status_code == 200)
    except Exception as e:
        logger.warning(f"Google AI connectivity test failed: {e}")
        return False


async def test_anthropic_connection(api_key: str) -> bool:
    """Test Anthropic API connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
            )
            return cast(bool, response.status_code == 200)
    except Exception as e:
        logger.warning(f"Anthropic connectivity test failed: {e}")
        return False


async def test_openrouter_connection(api_key: str) -> bool:
    """Test OpenRouter API connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://openrouter.ai/api/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return cast(bool, response.status_code == 200)
    except Exception as e:
        logger.warning(f"OpenRouter connectivity test failed: {e}")
        return False


async def test_grok_connection(api_key: str) -> bool:
    """Test Grok API connectivity"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.x.ai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            return cast(bool, response.status_code == 200)
    except Exception as e:
        logger.warning(f"Grok connectivity test failed: {e}")
        return False


PROVIDER_TESTERS = {
    "openai": test_openai_connection,
    "google": test_google_connection,
    "anthropic": test_anthropic_connection,
    "openrouter": test_openrouter_connection,
    "grok": test_grok_connection,
}


@router.get("/{provider}/status")
async def get_provider_status(
    provider: str = Path(
        ...,
        description="Provider name to test connectivity for",
        regex="^[a-z0-9_]+$",
        max_length=20
    )
):
    """Test provider connectivity using server-side API key (secure)"""
    try:
        # Basic provider validation
        allowed_providers = {"openai", "ollama", "google", "openrouter", "anthropic", "grok"}
        if provider not in allowed_providers:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid provider '{provider}'. Allowed providers: {sorted(allowed_providers)}"
            )

        # Basic sanitization for logging
        safe_provider = provider[:20]  # Limit length
        logger.info(f"Testing {safe_provider} connectivity server-side")

        if provider not in PROVIDER_TESTERS:
            raise HTTPException(
                status_code=400,
                detail=f"Provider '{provider}' not supported for connectivity testing"
            )

        # Determine which DB keys to check based on the provider
        provider_key_map = {
            "google": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "openai": ["OPENAI_API_KEY"],
            "anthropic": ["ANTHROPIC_API_KEY"],
            "openrouter": ["OPENROUTER_API_KEY"],
            "grok": ["GROK_API_KEY", "XAI_API_KEY"],
            "ollama": [] # Ollama doesn't need a key usually, or uses LLM_BASE_URL
        }

        keys_to_check = provider_key_map.get(provider, [])
        api_key = None

        if provider == "ollama":
             # Ollama "connection" is usually just checking the URL, but here we preserve the interface
             # We might need to fetch the base URL instead if the tester needed it, 
             # but the tester signature currently only takes api_key. 
             # For now, pass a dummy key for Ollama to allow the tester to proceed (if it handles URL internally or if we update it)
             # However, looking at the tester map, 'ollama' is NOT in PROVIDER_TESTERS in the current file state.
             # So we just skip if it's not supported.
             pass
        
        for key_name in keys_to_check:
            api_key = await credential_service.get_credential(key_name, decrypt=True)
            if api_key and str(api_key).strip():
                break
        
        # Special handling if no key found but required (Ollama might be an exception if supported later)
        if provider != "ollama" and (not api_key or not isinstance(api_key, str) or not api_key.strip()):
            logger.info(f"No API key configured for {safe_provider}")
            return {"ok": False, "reason": "no_key"}

        # Test connectivity using server-side key
        tester = PROVIDER_TESTERS[provider]
        is_connected = await tester(api_key)

        logger.info(f"{safe_provider} connectivity test result: {is_connected}")
        return {
            "ok": is_connected,
            "reason": "connected" if is_connected else "connection_failed",
            "provider": provider  # Echo back validated provider name
        }

    except HTTPException:
        # Re-raise HTTP exceptions (they're already properly formatted)
        raise
    except Exception as e:
        # Basic error sanitization for logging
        safe_error = str(e)[:100]  # Limit length
        logger.error(f"Error testing {provider[:20]} connectivity: {safe_error}")
        raise HTTPException(
            status_code=500, detail={"error": "Internal server error during connectivity test"}
        ) from e
