import time
from typing import Any

import aiohttp

from ...config.logfire_config import get_logger
from .models import _CACHE_TTL_SECONDS

logger = get_logger(__name__)
_provider_cache: dict[str, tuple[Any, float]] = {}


class DiscoveryEngine:
    """Core logic for model caching and tool testing."""

    @staticmethod
    def get_cached_result(cache_key: str) -> Any | None:
        if cache_key in _provider_cache:
            result, timestamp = _provider_cache[cache_key]
            if time.time() - timestamp < _CACHE_TTL_SECONDS:
                return result
        return None

    @staticmethod
    def cache_result(cache_key: str, result: Any) -> None:
        _provider_cache[cache_key] = (result, time.time())

    @staticmethod
    async def test_tool_support(model_name: str, api_url: str, session: aiohttp.ClientSession) -> bool:
        """Physical test for function calling support."""
        try:
            # Short timeout for testing
            async with session.post(
                f"{api_url}/v1/chat/completions",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": "test"}],
                    "tools": [{"type": "function", "function": {"name": "test", "parameters": {}}}],
                    "max_tokens": 1,
                },
                timeout=aiohttp.ClientTimeout(total=5),
            ) as response:
                return bool(response.status == 200)
        except Exception:
            return False
