"""
Provider status API endpoints for testing connectivity

Handles server-side provider connectivity testing without exposing API keys to frontend.
"""


import httpx
from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel, Field

from ..config.logfire_config import get_logger
from ..services.credential_service import credential_service
from ..services.credentials.provider_configs import _get_provider_api_key, _get_provider_base_url

logger = get_logger(__name__)
router = APIRouter(prefix="/api/providers", tags=["providers"])

class ProviderStatusResponse(BaseModel):
    ok: bool = Field(..., description="Whether the connectivity test passed")
    reason: str = Field(..., description="Reason for the result (e.g. connected, connection_failed, no_key)")
    provider: str | None = Field(None, description="The name of the provider tested")



async def test_provider_connection(provider: str, api_key: str, base_url: str) -> bool:
    """Unified tester for all supported LLM providers."""
    try:
        headers = {}
        if provider == "google":
            headers = {"x-goog-api-key": api_key}
        elif provider == "anthropic":
            headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
        else:
            headers = {"Authorization": f"Bearer {api_key}"}

        endpoint = f"{base_url.rstrip('/')}/models"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint, headers=headers)

            if response.status_code != 200:
                logger.warning(f"{provider.capitalize()} API Error Body: {response.text[:200]}")
            return bool(response.status_code == 200)

    except Exception as e:
        logger.warning(f"{provider.capitalize()} connectivity test failed: {e}")
        return False


@router.get("/{provider}/status", response_model=ProviderStatusResponse)
async def get_provider_status(
    provider: str = Path(
        ..., description="Provider name to test connectivity for", regex="^[a-z0-9_]+$", max_length=20
    ),
) -> ProviderStatusResponse:
    """Test provider connectivity using server-side API key (secure)"""
    try:
        # Supported providers for connectivity testing
        # Note: ollama is explicitly excluded from active testing here.
        supported_providers = {"openai", "google", "anthropic", "openrouter", "grok"} # 合法

        if provider not in supported_providers:
            if provider == "ollama":
                raise HTTPException(
                    status_code=400, detail="Provider 'ollama' not supported for connectivity testing"
                )
            raise HTTPException(
                status_code=400, detail=f"Invalid provider '{provider}'. Allowed: {sorted(supported_providers)}"
            )

        safe_provider = provider[:20]
        logger.info(f"Testing {safe_provider} connectivity server-side")

        # Get API key using the SSOT logic
        api_key = await _get_provider_api_key(credential_service, provider)

        if not api_key or not isinstance(api_key, str) or not api_key.strip():
            logger.info(f"No API key configured for {safe_provider}")
            return ProviderStatusResponse(ok=False, reason="no_key")

        # Get base URL using the SSOT logic
        # For testing, we pass an empty rag_settings since standard base URLs don't depend on it
        base_url = _get_provider_base_url(provider, {})
        if not base_url:
            logger.warning(f"No base URL configured for {safe_provider}")
            return ProviderStatusResponse(ok=False, reason="no_base_url")

        # Test connectivity using server-side key and unified tester
        is_connected = await test_provider_connection(provider, api_key, base_url)

        logger.info(f"{safe_provider} connectivity test result: {is_connected}")
        return ProviderStatusResponse(
            ok=is_connected,
            reason="connected" if is_connected else "connection_failed",
            provider=provider,
        )

    except HTTPException:
        raise
    except Exception as e:
        safe_error = str(e)[:100]
        logger.error(f"Error testing {provider[:20]} connectivity: {safe_error}")
        raise HTTPException(status_code=500, detail={"error": "Internal server error during connectivity test"}) from e
