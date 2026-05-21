from typing import Any, cast

import httpx

from ...config.logfire_config import get_logger

logger = get_logger(__name__)


async def execute_remote_rerank(
    agents_url: str, query: str, results: list[dict], content_key: str, top_k: int, fallback_strategy: Any = None
) -> list[dict]:
    """Performs reranking via remote agents service (Phase 4.6.28)."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{agents_url}/ml/rerank",
                json={
                    "query": query,
                    "results": results,
                    "content_key": content_key,
                    "top_k": top_k,
                },
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    logger.info("Remote reranking successful via Agents service.")
                    return cast(list[dict[str, Any]], data.get("results", []))

            logger.warning(f"Remote rerank failed (Status {response.status_code}). Falling back...")
    except Exception as e:
        logger.warning(f"Remote rerank connection error: {e}. Falling back...")

    # Fallback to local if available, else return original
    if fallback_strategy:
        fallback_results = await fallback_strategy.rerank_results(query, results, top_k=top_k, content_key=content_key)
        return cast(list[dict], fallback_results)
    return results[:top_k]
