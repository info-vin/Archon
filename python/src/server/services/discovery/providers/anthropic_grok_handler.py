

from ...config.logfire_config import get_logger
from ..models import ModelSpec

logger = get_logger(__name__)

async def discover_anthropic_models(api_key: str) -> list[ModelSpec]:
    """1:1 Physical Parity Implementation from ProviderDiscoveryService."""
    if not api_key:
        return []
    models = [
        ModelSpec("claude-3-5-sonnet-20241022", "anthropic", 200000, True, True, False, None, 3.00, 15.00, "Most intelligent Claude model"),
        ModelSpec("claude-3-5-haiku-20241022", "anthropic", 200000, True, False, False, None, 0.25, 1.25, "Fast and cost-effective Claude model"),
        ModelSpec("claude-3-opus-20240229", "anthropic", 200000, True, True, False, None, 15.00, 75.00, "Powerful model for complex tasks"),
        ModelSpec("claude-3-sonnet-20240229", "anthropic", 200000, True, True, False, None, 3.00, 15.00, "Balanced performance and cost"),
        ModelSpec("claude-3-haiku-20240307", "anthropic", 200000, True, False, False, None, 0.25, 1.25, "Fast responses and cost-effective"),
    ]
    logger.info(f"Discovered {len(models)} Anthropic models")
    return models

async def discover_grok_models(api_key: str) -> list[ModelSpec]:
    """1:1 Physical Parity Implementation from ProviderDiscoveryService."""
    if not api_key:
        return []
    models = [
        ModelSpec("grok-3-mini", "grok", 32768, True, True, False, None, 0.15, 0.60, "Fast and efficient Grok model"),
        ModelSpec("grok-3", "grok", 32768, True, True, False, None, 2.00, 10.00, "Standard Grok model"),
        ModelSpec("grok-4", "grok", 32768, True, True, False, None, 5.00, 25.00, "Advanced Grok model"),
        ModelSpec("grok-2-vision", "grok", 8192, True, True, True, None, 3.00, 15.00, "Grok model with vision capabilities"),
        ModelSpec("grok-2-latest", "grok", 8192, True, True, False, None, 2.00, 10.00, "Latest Grok 2 model"),
    ]
    logger.info(f"Discovered {len(models)} Grok models")
    return models
