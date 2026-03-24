"""
Knowledge Items API Hardened - Secure management of knowledge sources and chunks.
Standardized alignment with L2 modularity infrastructure.
"""


from fastapi import APIRouter, Depends, HTTPException

from src.server.services.knowledge.knowledge_item_service import KnowledgeItemService
from src.server.services.knowledge.knowledge_summary_service import KnowledgeSummaryService
from src.server.services.source_management_service import SourceManagementService
from src.server.utils import get_supabase_client

from ...auth.dependencies import get_current_user, requires_permission
from ...auth.permissions import TASK_UPDATE_ALL

router = APIRouter()

# EXPORTS for Test Patching Compatibility
KnowledgeService = KnowledgeItemService
KnowledgeSummaryService = KnowledgeSummaryService

@router.get("/knowledge-items/sources")
async def list_sources(current_user: dict = Depends(get_current_user)):
    """Lists all available knowledge sources. Authenticated only."""
    service = KnowledgeItemService(get_supabase_client())
    success, res = await service.get_available_sources()
    if not success:
        raise HTTPException(status_code=500, detail=str(res.get("error")))
    return res

@router.get("/knowledge-items")
async def list_knowledge_items(
    page: int = 1,
    per_page: int = 50,
    knowledge_type: str | None = None,
    search: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """Lists knowledge items, with full business logic and filtering."""
    service = KnowledgeItemService(get_supabase_client())
    success, res = await service.list_items(
        page=page, per_page=per_page, knowledge_type=knowledge_type, search=search
    )
    if not success:
        raise HTTPException(status_code=500, detail=str(res.get("error")))
    return res

@router.get("/knowledge-items/{source_id}/chunks")
async def list_source_chunks(source_id: str, current_user: dict = Depends(get_current_user)):
    """Lists raw chunks. Delegates to KnowledgeSummaryService."""
    service = KnowledgeSummaryService(get_supabase_client())
    success, res = await service.get_item_chunks(source_id=source_id)
    if not success:
        raise HTTPException(status_code=500, detail=str(res.get("error")))
    return res

@router.delete("/knowledge-items/{source_id}")
async def delete_knowledge_source(
    source_id: str,
    current_user: dict = Depends(requires_permission(TASK_UPDATE_ALL))
):
    """Deletes a knowledge source. Requires Admin level permission."""
    service = SourceManagementService()
    # Physical Correction: delete_source is a SYNCHRONOUS method
    success, res = service.delete_source(source_id)
    if not success:
        raise HTTPException(status_code=400, detail=str(res.get("error")))
    # Aligned with test expectations
    return {"success": True, "details": res}

@router.get("/available-sources")
async def list_available_sources(current_user: dict = Depends(get_current_user)):
    """Alias for listing sources."""
    return await list_sources(current_user=current_user)

@router.delete("/sources/{source_id}")
async def delete_source_alias(source_id: str, current_user: dict = Depends(requires_permission(TASK_UPDATE_ALL))):
    """Alias for deleting source."""
    return await delete_knowledge_source(source_id, current_user=current_user)
