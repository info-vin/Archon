from fastapi import APIRouter, Depends, HTTPException, status

from src.server.auth.dependencies import get_current_user
from src.server.models.auth_models import UserProfileDTO
from src.server.schemas.rag import (
    GraphPathResponse,
    GraphSearchRequest,
    GraphSearchResponse,
    RagChunkResponse,
    RagSearchRequest,
    RagSearchResponse,
)
from src.server.services.rag_service import RagService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/hybrid-search", response_model=RagSearchResponse)
async def hybrid_search(
    request: RagSearchRequest,
    current_user: UserProfileDTO = Depends(get_current_user),
):
    try:
        results = await RagService.hybrid_search(
            query=request.query,
            match_count=request.match_count,
            similarity_threshold=request.similarity_threshold,
            filter_dict=request.filter_dict,
            source_filter=request.source_filter,
            truncate_dim=request.truncate_dim,
            equipped_model=request.equipped_model,
            allow_react=request.allow_react,
        )
        parsed_results = [RagChunkResponse(**r) for r in results]
        return RagSearchResponse(status="success", results=parsed_results)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG search failed: {str(e)}",
        ) from e


@router.post("/graph-search", response_model=GraphSearchResponse)
async def graph_search(
    request: GraphSearchRequest,
    current_user: UserProfileDTO = Depends(get_current_user),
):
    try:
        results = await RagService.graph_search(
            start_entity_name=request.start_entity_name,
            max_hops=request.max_hops,
        )
        parsed_results = [GraphPathResponse(**r) for r in results]
        return GraphSearchResponse(status="success", results=parsed_results)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GraphRAG search failed: {str(e)}",
        ) from e
