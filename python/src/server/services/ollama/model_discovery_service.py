"""
Ollama Model Discovery Service

Provides comprehensive model discovery, validation, and capability detection for Ollama instances.
Supports multi-instance configurations with automatic dimension detection and health monitoring.
"""

import asyncio
import time
from typing import Any, cast

import httpx

from src.server.config.logfire_config import get_logger

from .discovery.models import InstanceHealthStatus, ModelCapabilities, OllamaModel

logger = get_logger(__name__)


class ModelDiscoveryService:
    """Service for discovering and validating Ollama models across multiple instances."""

    def __init__(self):
        self.model_cache: dict[str, list[OllamaModel]] = {}
        self.capability_cache: dict[str, ModelCapabilities] = {}
        self.health_cache: dict[str, InstanceHealthStatus] = {}
        self.cache_ttl = 300  # 5 minutes TTL
        self.discovery_timeout = 30  # 30 seconds timeout for discovery

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
        # ULTRA FAST MODE DISABLED - Now fetching real models
        # logger.warning(f"🚀 ULTRA FAST MODE ACTIVE - Returning mock models instantly for {instance_url}")

        # mock_models = [
        #     OllamaModel(
        #         name="llama3.2:latest",
        #         tag="llama3.2:latest",
        #         size=5000000000,
        #         digest="mock",
        #         capabilities=["chat", "structured_output"],
        #         instance_url=instance_url
        #     ),
        #     OllamaModel(
        #         name="mistral:latest",
        #         tag="mistral:latest",
        #         size=4000000000,
        #         digest="mock",
        #         capabilities=["chat"],
        #         instance_url=instance_url
        #     ),
        #     OllamaModel(
        #         name="nomic-embed-text:latest",
        #         tag="nomic-embed-text:latest",
        #         size=300000000,
        #         digest="mock",
        #         capabilities=["embedding"],
        #         embedding_dimensions=768,
        #         instance_url=instance_url
        #     ),
        #     OllamaModel(
        #         name="mxbai-embed-large:latest",
        #         tag="mxbai-embed-large:latest",
        #         size=670000000,
        #         digest="mock",
        #         capabilities=["embedding"],
        #         embedding_dimensions=1024,
        #         instance_url=instance_url
        #     ),
        # ]

        # return mock_models

        # Check cache first (but skip if we need detailed info)
        if not fetch_details:
            cached_models = self._get_cached_models(instance_url)
            if cached_models:
                return cached_models

        try:
            logger.info(f"Discovering models from Ollama instance: {instance_url}")

            # Use direct HTTP client for /api/tags endpoint (not OpenAI-compatible)
            async with httpx.AsyncClient(timeout=httpx.Timeout(self.discovery_timeout)) as client:
                # Remove /v1 suffix if present (OpenAI compatibility layer)
                base_url = instance_url.rstrip('/').replace('/v1', '')
                # Ollama API endpoint for listing models
                tags_url = f"{base_url}/api/tags"

                response = await client.get(tags_url)
                response.raise_for_status()
                data = response.json()

                models = []
                if "models" in data:
                    for model_data in data["models"]:
                        # Extract basic model information
                        model = OllamaModel(
                            name=model_data.get("name", "unknown"),
                            tag=model_data.get("name", "unknown"),  # Ollama uses name as tag
                            size=model_data.get("size", 0),
                            digest=model_data.get("digest", ""),
                            capabilities=[],  # Will be filled by capability detection
                            instance_url=instance_url
                        )

                        # Extract additional model details if available
                        details = model_data.get("details", {})
                        if details:
                            model.parameters = {
                                "family": details.get("family", ""),
                                "parameter_size": details.get("parameter_size", ""),
                                "quantization": details.get("quantization_level", "")
                            }

                        models.append(model)

                logger.info(f"Discovered {len(models)} models from {instance_url}")

                # Enrich models with capability information
                enriched_models = await self._enrich_model_capabilities(models, instance_url, fetch_details=fetch_details)

                # Cache the results
                self._cache_models(instance_url, enriched_models)

                return enriched_models

        except httpx.TimeoutException as e:
            logger.error(f"Timeout discovering models from {instance_url}")
            raise Exception(f"Timeout connecting to Ollama instance at {instance_url}") from e
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error discovering models from {instance_url}: {e.response.status_code}")
            raise Exception(f"HTTP {e.response.status_code} error from {instance_url}") from e
        except Exception as e:
            logger.error(f"Error discovering models from {instance_url}: {e}")
            raise Exception(f"Failed to discover models: {str(e)}") from e

    async def _enrich_model_capabilities(self, models: list[OllamaModel], instance_url: str, fetch_details: bool = False) -> list[OllamaModel]:
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

        start_time = time.time()
        status = InstanceHealthStatus(is_healthy=False)

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
                # Try to ping the Ollama API
                ping_url = f"{instance_url.rstrip('/')}/api/tags"

                response = await client.get(ping_url)
                response.raise_for_status()

                data = response.json()
                models_count = len(data.get("models", []))

                status.is_healthy = True
                status.response_time_ms = (time.time() - start_time) * 1000
                status.models_available = models_count
                status.last_checked = str(time.time())

                logger.debug(f"Instance {instance_url} is healthy: {models_count} models, {status.response_time_ms:.0f}ms")

        except httpx.TimeoutException:
            status.error_message = "Connection timeout"
            logger.warning(f"Health check timeout for {instance_url}")
        except httpx.HTTPStatusError as e:
            status.error_message = f"HTTP {e.response.status_code}"
            logger.warning(f"Health check HTTP error for {instance_url}: {e.response.status_code}")
        except Exception as e:
            status.error_message = str(e)
            logger.warning(f"Health check failed for {instance_url}: {e}")

        # Cache the result
        self.health_cache[cache_key] = status

        return status

    async def discover_models_from_multiple_instances(self, instance_urls: list[str], fetch_details: bool = False) -> dict[str, Any]:
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
                "discovery_errors": []
            }

        logger.info(f"Discovering models from {len(instance_urls)} Ollama instances with fetch_details={fetch_details}")

        # Discover models from all instances concurrently
        tasks = [self.discover_models(url, fetch_details=fetch_details) for url in instance_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
        all_models: list[OllamaModel] = []
        chat_models = []
        embedding_models = []
        host_status = {}
        discovery_errors = []

        for _i, (url, result) in enumerate(zip(instance_urls, results, strict=False)):
            if isinstance(result, Exception):
                error_msg = f"Failed to discover models from {url}: {str(result)}"
                discovery_errors.append(error_msg)
                host_status[url] = {"status": "error", "error": str(result)}
                logger.error(error_msg)
            else:
                # Use cast to tell type checker this is list[OllamaModel]
                models = cast(list[OllamaModel], result)
                all_models.extend(models)
                host_status[url] = {
                    "status": "online",
                    "models_count": str(len(models)),
                    "instance_url": url
                }

                # Categorize models
                for model in models:
                    if "chat" in model.capabilities:
                        chat_models.append({
                            "name": model.name,
                            "instance_url": model.instance_url,
                            "size": model.size,
                            "parameters": model.parameters,
                            # Real API data from /api/show - all 3 context values
                            "context_window": model.context_window,
                            "max_context_length": model.max_context_length,
                            "base_context_length": model.base_context_length,
                            "custom_context_length": model.custom_context_length,
                            "architecture": model.architecture,
                            "format": model.format,
                            "parent_model": model.parent_model,
                            "capabilities": model.capabilities
                        })

                    if "embedding" in model.capabilities:
                        embedding_models.append({
                            "name": model.name,
                            "instance_url": model.instance_url,
                            "dimensions": model.embedding_dimensions,
                            "size": model.size,
                            "parameters": model.parameters,
                            # Real API data from /api/show - all 3 context values
                            "context_window": model.context_window,
                            "max_context_length": model.max_context_length,
                            "base_context_length": model.base_context_length,
                            "custom_context_length": model.custom_context_length,
                            "architecture": model.architecture,
                            "format": model.format,
                            "parent_model": model.parent_model,
                            "capabilities": model.capabilities
                        })

        # Remove duplicates (same model on multiple instances)
        unique_models = {}
        for model in all_models:
            key = f"{model.name}@{model.instance_url}"
            unique_models[key] = model

        discovery_result = {
            "total_models": len(unique_models),
            "chat_models": chat_models,
            "embedding_models": embedding_models,
            "host_status": host_status,
            "discovery_errors": discovery_errors,
            "unique_model_names": list({model.name for model in unique_models.values()})
        }

        logger.info(f"Discovery complete: {discovery_result['total_models']} total models, "
                   f"{len(chat_models)} chat, {len(embedding_models)} embedding")

        return discovery_result


# Global service instance
model_discovery_service = ModelDiscoveryService()
