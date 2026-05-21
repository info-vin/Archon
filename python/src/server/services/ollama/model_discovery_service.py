"""
Ollama Model Discovery Service

Provides comprehensive model discovery, validation, and capability detection for Ollama instances.
Supports multi-instance configurations with automatic dimension detection and health monitoring.
"""

import asyncio
import time
from typing import Any

from src.server.config.logfire_config import get_logger

from .discovery.manifest_parser import OllamaManifestParser
from .discovery.models import InstanceHealthStatus, ModelCapabilities, OllamaModel
from .discovery.network_scanner import OllamaNetworkScanner

logger = get_logger(__name__)


class ModelDiscoveryService:
    """Service for discovering and validating Ollama models across multiple instances."""

    def __init__(self):
        self.model_cache: dict[str, list[OllamaModel]] = {}
        self.capability_cache: dict[str, ModelCapabilities] = {}
        self.capability_lock = asyncio.Lock()  # Restored for concurrency control
        self.health_cache: dict[str, InstanceHealthStatus] = {}
        self.cache_ttl = 300  # 5 minutes TTL
        self.scanner = OllamaNetworkScanner(timeout=30)
        self.parser = OllamaManifestParser()

    def _get_cached_models(self, instance_url: str) -> list[OllamaModel] | None:
        """Get cached models if not expired."""
        cache_key = f"models_{instance_url}"
        cached_data = self.model_cache.get(cache_key)
        if cached_data:
            # Check if any model in cache is still valid (simple TTL check)
            first_model = cached_data[0] if cached_data else None
            if first_model and first_model.last_updated:
                cache_time = float(first_model.last_updated)
                if time.time() - cache_time < self.cache_ttl:
                    logger.debug(f"Using cached models for {instance_url}")
                    return cached_data
                else:
                    # Expired, remove from cache
                    del self.model_cache[cache_key]
        return None

    def _cache_models(self, instance_url: str, models: list[OllamaModel]) -> None:
        """Cache models with current timestamp."""
        cache_key = f"models_{instance_url}"
        # Set timestamp for cache expiry
        current_time = str(time.time())
        for model in models:
            model.last_updated = current_time
        self.model_cache[cache_key] = models
        logger.debug(f"Cached {len(models)} models for {instance_url}")

    async def discover_models(self, instance_url: str, fetch_details: bool = False) -> list[OllamaModel]:
        """
        Discover all available models from an Ollama instance.

        Args:
            instance_url: Base URL of the Ollama instance
            fetch_details: If True, fetch comprehensive model details via /api/show

        Returns:
            List of OllamaModel objects with discovered capabilities
        """
        # Check cache first (but skip if we need detailed info)
        if not fetch_details:
            cached_models = self._get_cached_models(instance_url)
            if cached_models:
                return cached_models

        try:
            logger.info(f"Discovering models from Ollama instance: {instance_url}")

            # Use network scanner to fetch raw tags
            data = await self.scanner.fetch_tags(instance_url)

            # Use manifest parser to parse the tags
            models = self.parser.parse_tags_response(data, instance_url)

            logger.info(f"Discovered {len(models)} models from {instance_url}")

            # Enrich models with capability information
            enriched_models = await self._enrich_model_capabilities(models, instance_url, fetch_details=fetch_details)

            # Cache the results
            self._cache_models(instance_url, enriched_models)

            return enriched_models

        except Exception as e:
            logger.error(f"Error discovering models from {instance_url}: {e}")
            # The network_scanner raises standard exceptions which we propagate
            raise Exception(f"Failed to discover models: {str(e)}") from e

    async def _enrich_model_capabilities(
        self, models: list[OllamaModel], instance_url: str, fetch_details: bool = False
    ) -> list[OllamaModel]:
        """Pattern-match and enrich model capabilities. Delegates to capabilities submodule."""
        from .discovery.capabilities import enrich_model_capabilities_logic

        return await enrich_model_capabilities_logic(self, models, instance_url, fetch_details)

    async def _detect_model_capabilities_optimized(self, model_name: str, instance_url: str) -> ModelCapabilities:
        """Optimized capability detection. Delegates to capabilities submodule."""
        from .discovery.capabilities import detect_model_capabilities_logic

        return await detect_model_capabilities_logic(self, model_name, instance_url, optimized=True)

    async def _detect_model_capabilities(self, model_name: str, instance_url: str) -> ModelCapabilities:
        """Comprehensive capability detection. Delegates to capabilities submodule."""
        from .discovery.capabilities import detect_model_capabilities_logic

        return await detect_model_capabilities_logic(self, model_name, instance_url, optimized=False)

    # --- Private Facades for backward compatibility and testing ---
    async def _get_model_details(self, model_name: str, instance_url: str) -> dict[str, Any] | None:
        from .discovery.capabilities import get_model_details_logic

        return await get_model_details_logic(model_name, instance_url)

    async def _test_chat_capability(self, model_name: str, instance_url: str) -> bool:
        from .discovery.capabilities import test_chat_capability_logic

        return await test_chat_capability_logic(model_name, instance_url)

    async def _test_embedding_capability(self, model_name: str, instance_url: str) -> int | None:
        from .discovery.capabilities import test_embedding_capability_logic

        return await test_embedding_capability_logic(model_name, instance_url)

    async def _test_function_calling_capability(self, model_name: str, instance_url: str) -> bool:
        from .discovery.capabilities import test_function_calling_capability_logic

        return await test_function_calling_capability_logic(model_name, instance_url)

    async def _test_structured_output_capability(self, model_name: str, instance_url: str) -> bool:
        from .discovery.capabilities import test_structured_output_capability_logic

        return await test_structured_output_capability_logic(model_name, instance_url)

    async def _test_embedding_capability_fast(self, model_name: str, instance_url: str) -> int | None:
        from .discovery.capabilities import test_embedding_capability_fast_logic

        return await test_embedding_capability_fast_logic(model_name, instance_url)

    async def _test_chat_capability_fast(self, model_name: str, instance_url: str) -> bool:
        from .discovery.capabilities import test_chat_capability_fast_logic

        return await test_chat_capability_fast_logic(model_name, instance_url)

    async def _test_structured_output_capability_fast(self, model_name: str, instance_url: str) -> bool:
        from .discovery.capabilities import test_structured_output_capability_fast_logic

        return await test_structured_output_capability_fast_logic(model_name, instance_url)

    async def validate_model_capabilities(self, model_name: str, instance_url: str, required_capability: str) -> bool:
        """
        Validate that a model supports a required capability.

        Args:
            model_name: Name of the model to validate
            instance_url: Ollama instance URL
            required_capability: 'chat' or 'embedding'

        Returns:
            True if model supports the capability, False otherwise
        """
        try:
            capabilities = await self._detect_model_capabilities(model_name, instance_url)

            if required_capability == "chat":
                return capabilities.supports_chat
            elif required_capability == "embedding":
                return capabilities.supports_embedding
            elif required_capability == "function_calling":
                return capabilities.supports_function_calling
            elif required_capability == "structured_output":
                return capabilities.supports_structured_output
            else:
                logger.warning(f"Unknown capability requirement: {required_capability}")
                return False

        except Exception as e:
            logger.error(f"Error validating model {model_name} for {required_capability}: {e}")
            return False

    async def get_model_info(self, model_name: str, instance_url: str) -> OllamaModel | None:
        """
        Get comprehensive information about a specific model.

        Args:
            model_name: Name of the model
            instance_url: Ollama instance URL

        Returns:
            OllamaModel object with complete information or None if not found
        """
        try:
            models = await self.discover_models(instance_url)

            for model in models:
                if model.name == model_name:
                    return model

            logger.warning(f"Model {model_name} not found on instance {instance_url}")
            return None

        except Exception as e:
            logger.error(f"Error getting model info for {model_name}: {e}")
            return None

    async def check_instance_health(self, instance_url: str) -> InstanceHealthStatus:
        """
        Check the health status of an Ollama instance.

        Args:
            instance_url: Base URL of the Ollama instance

        Returns:
            InstanceHealthStatus with current health information
        """
        # Check cache first (shorter TTL for health checks)
        cache_key = f"health_{instance_url}"
        if cache_key in self.health_cache:
            cached_health = self.health_cache[cache_key]
            if cached_health.last_checked:
                cache_time = float(cached_health.last_checked)
                # Use shorter cache for health (30 seconds)
                if time.time() - cache_time < 30:
                    return cached_health

        status = InstanceHealthStatus(is_healthy=False)
        is_healthy, response_time_ms, models_count, error_message = await self.scanner.ping_health(instance_url)

        if is_healthy:
            status.is_healthy = True
            status.response_time_ms = response_time_ms
            status.models_available = models_count
            status.last_checked = str(time.time())
            logger.debug(f"Instance {instance_url} is healthy: {models_count} models, {status.response_time_ms:.0f}ms")
        else:
            status.error_message = error_message
            logger.warning(f"Health check failed for {instance_url}: {error_message}")

        # Cache the result
        self.health_cache[cache_key] = status

        return status

    async def discover_models_from_multiple_instances(
        self, instance_urls: list[str], fetch_details: bool = False
    ) -> dict[str, Any]:
        """
        Discover models from multiple Ollama instances concurrently.

        Args:
            instance_urls: List of Ollama instance URLs
            fetch_details: If True, fetch comprehensive model details via /api/show

        Returns:
            Dictionary with discovery results and aggregated information
        """
        if not instance_urls:
            return {
                "total_models": 0,
                "chat_models": [],
                "embedding_models": [],
                "host_status": {},
                "discovery_errors": [],
            }

        logger.info(f"Discovering models from {len(instance_urls)} Ollama instances with fetch_details={fetch_details}")

        # Discover models from all instances concurrently
        tasks = [self.discover_models(url, fetch_details=fetch_details) for url in instance_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Delegate aggregation to the parser
        discovery_result = self.parser.aggregate_discovery_results(instance_urls, results)

        logger.info(
            f"Discovery complete: {discovery_result['total_models']} total models, "
            f"{len(discovery_result['chat_models'])} chat, {len(discovery_result['embedding_models'])} embedding"
        )

        return discovery_result


# Global service instance
model_discovery_service = ModelDiscoveryService()
