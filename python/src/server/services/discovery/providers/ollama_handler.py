from urllib.parse import urlparse

import aiohttp

from ...config.logfire_config import get_logger
from ..models import (
    EMBEDDING_DIMENSIONS,
    EMBEDDING_MODEL_PATTERNS,
    MODEL_CONTEXT_WINDOWS,
    VISION_MODEL_PATTERNS,
    ModelSpec,
)

logger = get_logger(__name__)


async def discover_ollama_models(base_urls: list[str], session: aiohttp.ClientSession, test_tool_fn) -> list[ModelSpec]:
    """1:1 Physical Parity Implementation from ProviderDiscoveryService."""
    all_models = []
    for base_url in base_urls:
        try:
            parsed = urlparse(base_url)
            api_url = base_url.replace("/v1", "") if parsed.path.endswith("/v1") else base_url

            async with session.get(f"{api_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model_info in data.get("models", []):
                        full_name = model_info.get("name", "")
                        model_name = full_name.split(":")[0]

                        supports_tools = await test_tool_fn(model_name, api_url)
                        supports_vision = any(p in model_name.lower() for p in VISION_MODEL_PATTERNS)
                        supports_embeddings = any(p in model_name.lower() for p in EMBEDDING_MODEL_PATTERNS)

                        context_window = 4096
                        for family, window_size in MODEL_CONTEXT_WINDOWS.items():
                            if family in model_name.lower():
                                context_window = window_size
                                break

                        embedding_dims = next(
                            (dims for pattern, dims in EMBEDDING_DIMENSIONS.items() if pattern in model_name.lower()),
                            None,
                        )

                        models.append(
                            ModelSpec(
                                name=full_name,
                                provider="ollama",
                                context_window=context_window,
                                supports_tools=supports_tools,
                                supports_vision=supports_vision,
                                supports_embeddings=supports_embeddings,
                                embedding_dimensions=embedding_dims,
                                description=f"Ollama model on {base_url}",
                                aliases=[model_name] if ":" in full_name else [],
                            )
                        )
                    all_models.extend(models)
                    logger.info(f"Discovered {len(models)} Ollama models from {base_url}")
        except Exception as e:
            logger.error(f"Error discovering Ollama models from {base_url}: {e}")
    return all_models
