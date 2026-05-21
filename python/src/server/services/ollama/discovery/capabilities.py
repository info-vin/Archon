"""
Capability Detection Engine for Ollama Discovery Service (Phase 4.6.12 Hardening)

Handles model capability testing (chat, embedding, structured output),
metadata enrichment via /api/show, and pattern matching.
"""

from typing import cast

from src.server.config.logfire_config import get_logger

from .capability_patterns import enrich_model_capabilities_logic
from .capability_tester import (
    get_model_details_logic,
    test_chat_capability_fast_logic,
    test_chat_capability_logic,
    test_embedding_capability_fast_logic,
    test_embedding_capability_logic,
    test_function_calling_capability_logic,
    test_structured_output_capability_fast_logic,
    test_structured_output_capability_logic,
)
from .models import ModelCapabilities

logger = get_logger(__name__)

# Expose enrich_model_capabilities_logic for backwards compatibility and easy import
__all__ = [
    "enrich_model_capabilities_logic",
    "detect_model_capabilities_logic",
    "get_model_details_logic",
    "test_chat_capability_logic",
    "test_embedding_capability_logic",
    "test_function_calling_capability_logic",
    "test_structured_output_capability_logic",
    "test_chat_capability_fast_logic",
    "test_embedding_capability_fast_logic",
    "test_structured_output_capability_fast_logic",
]


async def detect_model_capabilities_logic(
    service_instance, model_name: str, instance_url: str, optimized: bool = False
) -> ModelCapabilities:
    """Detect capabilities with CONCURRENCY LOCK."""
    cache_key = f"{model_name}@{instance_url}"

    async with service_instance.capability_lock:
        if cache_key in service_instance.capability_cache:
            return cast(ModelCapabilities, service_instance.capability_cache[cache_key])

    async with service_instance.capability_lock:
        if cache_key in service_instance.capability_cache:
            return cast(ModelCapabilities, service_instance.capability_cache[cache_key])

        caps = ModelCapabilities()
        try:
            if optimized:
                if any(p in model_name.lower() for p in ["embed", "embedding"]):
                    dims = await test_embedding_capability_fast_logic(model_name, instance_url)
                    if dims:
                        caps.supports_embedding = True
                        caps.embedding_dimensions = dims
                        service_instance.capability_cache[cache_key] = caps
                        return caps

                if await test_chat_capability_fast_logic(model_name, instance_url):
                    caps.supports_chat = True
                    if await test_structured_output_capability_fast_logic(model_name, instance_url):
                        caps.supports_structured_output = True
            else:
                dims = await test_embedding_capability_logic(model_name, instance_url)
                if dims:
                    caps.supports_embedding = True
                    caps.embedding_dimensions = dims

                if await test_chat_capability_logic(model_name, instance_url):
                    caps.supports_chat = True
                    if await test_function_calling_capability_logic(model_name, instance_url):
                        caps.supports_function_calling = True
                    if await test_structured_output_capability_logic(model_name, instance_url):
                        caps.supports_structured_output = True

            info = await get_model_details_logic(model_name, instance_url)
            if info:
                caps.parameter_count = info.get("parameter_count")
                caps.model_family = info.get("family")
                caps.quantization = info.get("quantization")

            service_instance.capability_cache[cache_key] = caps
        except Exception as e:
            logger.warning(f"Capability detection failed for {model_name}: {e}")
            caps.supports_chat = True

        return caps
