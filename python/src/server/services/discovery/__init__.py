"""
Provider Discovery Package (Facade Pattern)
Standardized L2 Modularization for Phase 4.6.24.
"""

import logging
import time
from typing import Any, cast

import aiohttp

from ..credential_service import credential_service
from .engine import DiscoveryEngine
from .models import ModelSpec, ProviderStatus

logger = logging.getLogger(__name__)


class ProviderDiscoveryService:
    """Facade for multi-provider AI model discovery and health checking."""

    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        if self._session:
            await self._session.close()

    async def discover_openai_models(self, api_key: str) -> list[ModelSpec]:
        from .providers.openai_handler import discover_openai_models

        cache_key = f"openai_{hash(api_key)}"
        cached = DiscoveryEngine.get_cached_result(cache_key)
        if cached:
            return cast(list[ModelSpec], cached)

        models = await discover_openai_models(api_key)
        DiscoveryEngine.cache_result(cache_key, models)
        return models

    async def discover_google_models(self, api_key: str) -> list[ModelSpec]:
        from .providers.google_handler import discover_google_models

        cache_key = f"google_{hash(api_key)}"
        cached = DiscoveryEngine.get_cached_result(cache_key)
        if cached:
            return cast(list[ModelSpec], cached)

        session = await self._get_session()
        models = await discover_google_models(api_key, session)
        DiscoveryEngine.cache_result(cache_key, models)
        return models

    async def discover_ollama_models(self, base_urls: list[str]) -> list[ModelSpec]:
        from .providers.ollama_handler import discover_ollama_models

        session = await self._get_session()
        return await discover_ollama_models(base_urls, session, DiscoveryEngine.test_tool_support)

    async def check_provider_health(self, provider: str, config: dict[str, Any]) -> ProviderStatus:
        """Physical Parity: End-to-end health check for a provider."""
        start_time = time.time()
        try:
            api_key = config.get("api_key")
            models = []
            if provider == "openai" and isinstance(api_key, str):
                models = await self.discover_openai_models(api_key)
            elif provider == "google" and isinstance(api_key, str):
                models = await self.discover_google_models(api_key)

            return ProviderStatus(
                provider=provider,
                is_available=len(models) > 0,
                response_time_ms=(time.time() - start_time) * 1000,
                models_available=len(models),
                last_checked=time.time(),
            )
        except Exception as e:
            return ProviderStatus(provider=provider, is_available=False, error_message=str(e), last_checked=time.time())

    async def get_all_available_models(self) -> dict[str, list[ModelSpec]]:
        """Consolidated discovery logic."""
        results: dict[str, list[ModelSpec]] = {}
        openai_key = await credential_service.get_credential("OPENAI_API_KEY")
        if isinstance(openai_key, str):
            results["openai"] = await self.discover_openai_models(openai_key)
        return results


# Global singleton instance for the application
provider_discovery_service = ProviderDiscoveryService()
