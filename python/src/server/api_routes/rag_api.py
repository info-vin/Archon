from fastapi import APIRouter, Depends, HTTPException, status

from src.server.auth.dependencies import get_current_user
from src.server.schemas.rag import RagChunkResponse, RagSearchRequest, RagSearchResponse
from src.server.services.rag_service import RagService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/hybrid-search", response_model=RagSearchResponse)
async def hybrid_search(
    request: RagSearchRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        results = await RagService.hybrid_search(
            query=request.query,
            match_count=request.match_count,
            similarity_threshold=request.similarity_threshold,
            filter_dict=request.filter_dict,
            source_filter=request.source_filter,
        )
        parsed_results = [RagChunkResponse(**r) for r in results]
        return RagSearchResponse(status="success", results=parsed_results)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG search failed: {str(e)}",
        ) from e
