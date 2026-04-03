
import logging
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# Physical import from the shared volume
from src.server.services.search.reranking_strategy import reranking_strategy

logger = logging.getLogger(__name__)
router = APIRouter()

class RerankRequest(BaseModel):
    query: str
    documents: list[dict[str, Any]]
    content_key: str = "content"
    top_k: int = 5

@router.post("/rerank")
async def rerank_documents(request: RerankRequest):
    """
    Physically grounded reranking endpoint.
    Offloads heavy ML computation from main server.
    """
    try:
        if not reranking_strategy.is_available():
            logger.error("Reranking model not available in Agents container.")
            return {"success": False, "error": "ML Model not loaded"}

        results = await reranking_strategy.rerank_results(
            query=request.query,
            results=request.documents,
            content_key=request.content_key,
            top_k=request.top_k,
        )
        return {"success": True, "results": results}
    except Exception as e:
        logger.error(f"Remote Reranking failed: {e}")
        return {"success": False, "error": str(e)}
