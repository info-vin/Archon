from typing import cast

from fastapi import APIRouter, Depends, Header, HTTPException

from src.server.api_routes.knowledge.schemas import KnowledgeItemRequest
from src.server.auth.dependencies import get_current_user
from src.server.config.logfire_config import get_logger, safe_logfire_error
from src.server.services.knowledge.knowledge_item_service import KnowledgeItemService
from src.server.utils import get_supabase_client

router = APIRouter()
logger = get_logger(__name__)

@router.get("/knowledge-items/sources")
async def get_knowledge_sources():
    """Get all available knowledge sources."""
    try:
        service = KnowledgeItemService(get_supabase_client())
        success, result = await service.get_available_sources()
        if not success:
            raise HTTPException(status_code=500, detail=str(result.get("error")))
        return result
    except Exception as e:
        safe_logfire_error(f"Failed to get knowledge sources | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/knowledge-items")
async def get_knowledge_items(
    page: int = 1,
    per_page: int = 50,
    knowledge_type: str | None = None,
    search: str | None = None,
):
    """List all knowledge items with pagination and filtering."""
    try:
        service = KnowledgeItemService(get_supabase_client())
        success, result = await service.list_items(
            page=page, per_page=per_page, knowledge_type=knowledge_type, search=search
        )
        if not success:
            raise HTTPException(status_code=500, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(f"Failed to list knowledge items | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/knowledge-items/{source_id}/chunks")
async def get_knowledge_item_chunks(
    source_id: str,
    page: int = 1,
    limit: int = 50,
    domain_filter: str | None = None,
):
    """Get content chunks for a specific knowledge item."""
    try:
        # CORRECT PHYSICAL SERVICE: KnowledgeSummaryService
        from src.server.services.knowledge.knowledge_summary_service import KnowledgeSummaryService
        service = KnowledgeSummaryService(get_supabase_client())
        success, result = await service.get_item_chunks(
            source_id=source_id, page=page, per_page=limit, domain_filter=domain_filter
        )
        if not success:
            raise HTTPException(status_code=500, detail=result.get("error"))
        return result
    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(f"Failed to get item chunks {source_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.put("/knowledge-items/{source_id}")
async def update_knowledge_item(
    source_id: str,
    request: KnowledgeItemRequest,
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    current_user: dict = Depends(get_current_user)
):
    """Update a knowledge item's metadata."""
    if x_user_role:
        from server.services.rbac_service import RBACService
        rbac_service = RBACService()
        if not rbac_service.can_manage_content(x_user_role):
            raise HTTPException(status_code=403, detail="Forbidden: Permission denied")

    try:
        service = KnowledgeItemService(get_supabase_client())
        update_data = {k: v for k, v in request.model_dump().items() if v is not None}
        success, result = await service.update_item(source_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail=result.get("error"))
        return result
    except Exception as e:
        safe_logfire_error(f"Failed to update knowledge item {source_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/knowledge-items/{source_id}")
async def delete_knowledge_item(
    source_id: str,
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    current_user: dict = Depends(get_current_user)
):
    """Delete a knowledge item and its associated data."""
    if x_user_role:
        from server.services.rbac_service import RBACService
        rbac_service = RBACService()
        if not rbac_service.can_manage_content(x_user_role):
            raise HTTPException(status_code=403, detail="Forbidden: Permission denied")

    try:
        from src.server.services.source_management_service import SourceManagementService
        source_service = SourceManagementService(get_supabase_client())
        success, result_data = source_service.delete_source(source_id)
        if not success:
            raise HTTPException(status_code=500, detail=str(result_data.get("error")))
        return {"success": True, "message": f"Source {source_id} deleted successfully"}
    except Exception as e:
        safe_logfire_error(f"Failed to delete knowledge item {source_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/available-sources")
async def get_available_sources(current_user: dict = Depends(get_current_user)):
    """Get all available sources for RAG queries."""
    try:
        service = KnowledgeItemService(get_supabase_client())
        success, result = await service.get_available_sources()
        if not success:
            err_msg = str(cast(dict, result).get("error", "Unknown error"))
            raise HTTPException(status_code=500, detail=err_msg)
        return result
    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(f"Failed to get available sources | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/sources/{source_id}")
async def delete_source(source_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a source and all its related chunks and data."""
    try:
        from src.server.services.source_management_service import SourceManagementService
        service = SourceManagementService(get_supabase_client())
        success, _ = service.delete_source(source_id)
        return {"success": success, "message": f"Source {source_id} processing completed"}
    except Exception as e:
        safe_logfire_error(f"Failed to delete source {source_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
