import logging
from typing import Any

from fastapi import APIRouter

from src.server.models.knowledge_models import RerankRequest, RerankResponse

# Physical import from the shared volume
from src.server.services.search.reranking_strategy import reranking_strategy

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/rerank", response_model=RerankResponse)
async def rerank_documents(request: RerankRequest) -> RerankResponse:
    """
    Physically grounded reranking endpoint.
    Offloads heavy ML computation from main server.
    """
    try:
        if not reranking_strategy.is_available():
            logger.error("Reranking model not available in Agents container.")
            return RerankResponse(success=False, error="ML Model not loaded")

        results: list[dict[str, Any]] = await reranking_strategy.rerank_results(
            query=request.query,
            results=request.results,
            content_key=request.content_key,
            top_k=request.top_k,
        )
        return RerankResponse(success=True, results=results)
    except Exception as e:
        logger.error(f"Remote Reranking failed: {e}")
        return RerankResponse(success=False, error=str(e))
