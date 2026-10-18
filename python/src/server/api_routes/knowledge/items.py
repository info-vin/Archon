"""
Knowledge Items API Hardened - Secure management of knowledge sources and chunks.
Standardized alignment with L2 modularity infrastructure.
"""

from fastapi import APIRouter, Depends, HTTPException

from src.server.models.auth_models import UserProfileDTO
from src.server.services.knowledge.knowledge_item_service import KnowledgeItemService
from src.server.services.knowledge.knowledge_summary_service import KnowledgeSummaryService
from src.server.services.source_management_service import SourceManagementService
from src.server.utils import get_supabase_client

from ...auth.dependencies import requires_permission
from ...auth.permissions import TASK_READ_OWN, TASK_READ_TEAM, TASK_UPDATE_ALL
from .schemas import (
    AvailableSourcesResponse,
    ChunkPagination,
    DeleteSourceResponse,
    KnowledgeItemListResponse,
    SourceChunksResponse,
)

router = APIRouter()

# EXPORTS for Test Patching Compatibility
KnowledgeService = KnowledgeItemService
KnowledgeSummaryService = KnowledgeSummaryService


@router.get("/knowledge-items/sources", response_model=AvailableSourcesResponse)
async def list_sources(
    current_user: UserProfileDTO = Depends(requires_permission(TASK_READ_OWN)),
) -> AvailableSourcesResponse:
    """Lists all available knowledge sources. Requires TASK_READ_OWN."""
    service = KnowledgeItemService(get_supabase_client())
    success, res = await service.get_available_sources()
    if not success:
        raise HTTPException(status_code=500, detail=str(res.get("error") if isinstance(res, dict) else res))
    if isinstance(res, list):
        return AvailableSourcesResponse(sources=res)
    return AvailableSourcesResponse.model_validate(res)


@router.get("/knowledge-items", response_model=KnowledgeItemListResponse)
async def list_knowledge_items(
    page: int = 1,
    per_page: int = 50,
    knowledge_type: str | None = None,
    search: str | None = None,
    current_user: UserProfileDTO = Depends(requires_permission(TASK_READ_OWN)),
) -> KnowledgeItemListResponse:
    """Lists knowledge items. Requires TASK_READ_OWN."""
    service = KnowledgeItemService(get_supabase_client())
    success, res = await service.list_items(page=page, per_page=per_page, knowledge_type=knowledge_type, search=search)
    if not success:
        raise HTTPException(status_code=500, detail=str(res.get("error") if isinstance(res, dict) else res))
    if isinstance(res, list):
        return KnowledgeItemListResponse(items=res, total=len(res), page=page, per_page=per_page)
    return KnowledgeItemListResponse.model_validate(res)


@router.get("/knowledge-items/{source_id}/chunks", response_model=SourceChunksResponse)
async def list_source_chunks(
    source_id: str,
    page: int = 1,
    per_page: int = 50,
    domain_filter: str | None = None,
    current_user: UserProfileDTO = Depends(requires_permission(TASK_READ_TEAM)),
) -> SourceChunksResponse:
    """Lists raw chunks. Requires TASK_READ_TEAM."""
    service = KnowledgeSummaryService(get_supabase_client())
    success, res = await service.get_item_chunks(
        source_id=source_id, page=page, per_page=per_page, domain_filter=domain_filter
    )
    if not success:
        raise HTTPException(status_code=500, detail=str(res.get("error") if isinstance(res, dict) else res))
    if isinstance(res, list):
        return SourceChunksResponse(
            chunks=res,
            pagination=ChunkPagination(
                total=len(res), page=page, per_page=per_page, total_pages=1 if res else 0
            ),
        )
    return SourceChunksResponse.model_validate(res)


@router.delete("/knowledge-items/{source_id}", response_model=DeleteSourceResponse)
async def delete_knowledge_source(
    source_id: str, current_user: UserProfileDTO = Depends(requires_permission(TASK_UPDATE_ALL))
) -> DeleteSourceResponse:
    """Deletes a knowledge source. Requires Admin level permission."""
    service = SourceManagementService()
    # Physical Correction: delete_source is a SYNCHRONOUS method
    success, res = service.delete_source(source_id)
    if not success:
        raise HTTPException(status_code=400, detail=str(res.get("error")))
    # Aligned with test expectations
    return DeleteSourceResponse(success=True, details=res)


@router.get("/available-sources", response_model=AvailableSourcesResponse)
async def list_available_sources(
    current_user: UserProfileDTO = Depends(requires_permission(TASK_READ_OWN)),
) -> AvailableSourcesResponse:
    """Alias for listing sources. Requires TASK_READ_OWN."""
    return await list_sources(current_user=current_user)


@router.delete("/sources/{source_id}", response_model=DeleteSourceResponse)
async def delete_source_alias(
    source_id: str, current_user: UserProfileDTO = Depends(requires_permission(TASK_UPDATE_ALL))
) -> DeleteSourceResponse:
    """Alias for deleting source."""
    return await delete_knowledge_source(source_id, current_user=current_user)
