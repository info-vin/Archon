from typing import Any

import aiohttp

from src.server.config.config import get_config
from src.server.config.logfire_config import get_logger

from ..models import ModelSpec

logger = get_logger(__name__)

async def discover_google_models(api_key: str, session: aiohttp.ClientSession) -> list[ModelSpec]:
    """1:1 Physical Parity Implementation from ProviderDiscoveryService."""
    models = []
    try:
        base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        headers = {"x-goog-api-key": api_key}

        pricing_db = get_config().token_pricing

        # Hardcode some known context window/feature metadata that API might not reliably expose in a way we want
        # We only use this for models that exist in BOTH API and pricing_db.
        FEATURE_MAP: dict[str, dict[str, Any]] = {
            "gemini-1.5-pro": {"context": 2097152, "tools": True, "vision": True, "emb": False, "dim": None, "desc": "Advanced reasoning and multimodal capabilities"},
            "gemini-1.5-flash": {"context": 1048576, "tools": True, "vision": True, "emb": False, "dim": None, "desc": "Fast and versatile performance"},
            "gemini-3.1-pro": {"context": 2097152, "tools": True, "vision": True, "emb": False, "dim": None, "desc": "Latest advanced reasoning model"},
            "gemini-3.1-flash": {"context": 1048576, "tools": True, "vision": True, "emb": False, "dim": None, "desc": "Latest high-performance flash model"},
            "gemini-3.1-flash-lite": {"context": 1048576, "tools": True, "vision": True, "emb": False, "dim": None, "desc": "Free Tier / Ultra-fast lite"},
            "gemini-2.0-flash": {"context": 1048576, "tools": True, "vision": True, "emb": False, "dim": None, "desc": "Next-gen flash model"},
            "gemini-2.5-flash": {"context": 1048576, "tools": True, "vision": True, "emb": False, "dim": None, "desc": "Latest high-performance flash model"},
            "gemini-2.5-flash-lite": {"context": 1048576, "tools": True, "vision": True, "emb": False, "dim": None, "desc": "Ultra-fast lite model"},
            "gemini-2.0-flash-lite-preview-02-05": {"context": 1048576, "tools": True, "vision": True, "emb": False, "dim": None, "desc": "Free Tier / Next-gen preview"},
            "gemini-1.0-pro": {"context": 30720, "tools": True, "vision": False, "emb": False, "dim": None, "desc": "Efficient model for text tasks"},
            "text-embedding-004": {"context": 2048, "tools": False, "vision": False, "emb": True, "dim": 768, "desc": "Google's latest embedding model"},
        }

        async with session.get(base_url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                active_model_names = [m["name"].split("/")[-1] for m in data.get("models", [])]

                for name in active_model_names:
                    if name in pricing_db:
                        cost = pricing_db[name]
                        features = FEATURE_MAP.get(name, {"context": 1048576, "tools": True, "vision": False, "emb": False, "dim": None, "desc": "Dynamically discovered model"})

                        models.append(
                            ModelSpec(
                                name=name,
                                provider="google",
                                context_window=features["context"],
                                supports_tools=features["tools"],
                                supports_vision=features["vision"],
                                supports_embeddings=features["emb"],
                                embedding_dimensions=features["dim"],
                                pricing_input=cost.get("input", 0.0),
                                pricing_output=cost.get("output", 0.0),
                                description=features["desc"]
                            )
                        )

                logger.info(f"Discovered {len(models)} Google models after SSOT filtering")
            else:
                logger.warning(f"Google API returned status {response.status}")
    except Exception as e:
        logger.error(f"Error discovering Google models: {e}")
    return models
