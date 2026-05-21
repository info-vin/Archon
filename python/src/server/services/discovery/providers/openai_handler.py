import openai

from ...config.logfire_config import get_logger
from ..models import ModelSpec

logger = get_logger(__name__)


async def discover_openai_models(api_key: str) -> list[ModelSpec]:
    """1:1 Physical Parity Implementation from ProviderDiscoveryService."""
    models = []
    try:
        client = openai.AsyncOpenAI(api_key=api_key)
        response = await client.models.list()

        model_specs = {
            "gpt-4o": ModelSpec(
                "gpt-4o", "openai", 128000, True, True, False, None, 2.50, 10.00, "Most capable GPT-4 model with vision"
            ),
            "gpt-4o-mini": ModelSpec(
                "gpt-4o-mini", "openai", 128000, True, True, False, None, 0.15, 0.60, "Affordable GPT-4 model"
            ),
            "gpt-4-turbo": ModelSpec(
                "gpt-4-turbo", "openai", 128000, True, True, False, None, 10.00, 30.00, "GPT-4 Turbo with vision"
            ),
            "gpt-3.5-turbo": ModelSpec(
                "gpt-3.5-turbo", "openai", 16385, True, False, False, None, 0.50, 1.50, "Fast and efficient model"
            ),
            "text-embedding-3-large": ModelSpec(
                "text-embedding-3-large",
                "openai",
                8191,
                False,
                False,
                True,
                3072,
                0.13,
                0,
                "High-quality embedding model",
            ),
            "text-embedding-3-small": ModelSpec(
                "text-embedding-3-small", "openai", 8191, False, False, True, 1536, 0.02, 0, "Efficient embedding model"
            ),
            "text-embedding-ada-002": ModelSpec(
                "text-embedding-ada-002", "openai", 8191, False, False, True, 1536, 0.10, 0, "Legacy embedding model"
            ),
        }

        for model in response.data:
            if model.id in model_specs:
                models.append(model_specs[model.id])
            else:
                models.append(
                    ModelSpec(
                        name=model.id, provider="openai", context_window=4096, description=f"OpenAI model {model.id}"
                    )
                )

        logger.info(f"Discovered {len(models)} OpenAI models")
    except Exception as e:
        logger.error(f"Error discovering OpenAI models: {e}")
    return models
