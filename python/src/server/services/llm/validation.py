import time
from typing import Any

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


async def validate_provider_instance(provider: str, instance_url: str | None = None) -> dict[str, Any]:
    """Validate a provider instance and return health information."""
    # Late import to avoid circular dependency and match test patch points
    from ..llm_provider_service import get_llm_client

    try:
        if provider == "ollama":
            from ..ollama.model_discovery_service import model_discovery_service

            if not instance_url:
                from ...schemas.settings import NetworkConfig
                from ...services.settings_service import SettingsService
                try:
                    net_config = NetworkConfig.model_validate(SettingsService().get_all_settings())
                    instance_url = net_config.ollama_base_url
                except Exception:
                    instance_url = NetworkConfig().ollama_base_url

            health = await model_discovery_service.check_instance_health(instance_url)
            return {
                "provider": provider,
                "instance_url": instance_url,
                "is_available": health.is_healthy,
                "response_time_ms": health.response_time_ms,
                "models_available": health.models_available,
                "validation_timestamp": time.time(),
            }

        async with get_llm_client(provider=provider) as client:
            start = time.time()
            models_count = 0

            if provider == "openai":
                models = await client.models.list()
                models_count = len(models.data)
            elif provider == "anthropic":
                # Anthropic validation restored from original logic
                models_count = 1
            else:
                models_count = 1

            return {
                "provider": provider,
                "is_available": True,
                "response_time_ms": (time.time() - start) * 1000,
                "models_available": models_count,
                "validation_timestamp": time.time(),
            }

    except Exception as e:
        logger.error(f"Error validating provider {provider}: {e}")
        return {
            "provider": provider,
            "is_available": False,
            "error_message": str(e),
            "validation_timestamp": time.time(),
        }
