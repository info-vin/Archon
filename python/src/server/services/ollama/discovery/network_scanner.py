import time
from typing import Any, cast

import httpx

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)

class OllamaNetworkScanner:
    """Handles network communication with Ollama instances."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    async def fetch_tags(self, instance_url: str) -> dict[str, Any]:
        """Fetches the raw JSON response from the /api/tags endpoint."""
        async with httpx.AsyncClient(timeout=httpx.Timeout(self.timeout)) as client:
            base_url = instance_url.rstrip("/").replace("/v1", "")
            tags_url = f"{base_url}/api/tags"
            response = await client.get(tags_url)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())

    async def ping_health(self, instance_url: str) -> tuple[bool, float, int, str]:
        """Pings the instance to check health. Returns (is_healthy, response_time_ms, models_count, error_message)"""
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(10)) as client:
                ping_url = f"{instance_url.rstrip('/')}/api/tags"
                response = await client.get(ping_url)
                response.raise_for_status()
                data = response.json()
                models_count = len(data.get("models", []))
                response_time_ms = (time.time() - start_time) * 1000
                return True, response_time_ms, models_count, ""
        except httpx.TimeoutException:
            return False, 0.0, 0, "Connection timeout"
        except httpx.HTTPStatusError as e:
            return False, 0.0, 0, f"HTTP {e.response.status_code}"
        except Exception as e:
            return False, 0.0, 0, str(e)
