
from fastapi import APIRouter

from ..schemas.knowledge import DatabaseMetricsResponse, KnowledgeItemsResponse

# EXPORTS for test compatibility (GAP-012)
from ..services.storage.storage_services import storage_service
from ..utils import get_supabase_client
from .knowledge import active_crawl_tasks
from .knowledge.crawling import router as crawling_router
from .knowledge.items import router as items_router
from .knowledge.search import router as search_router
from .knowledge.upload import router as upload_router
from .knowledge.upload import upload_document

# PHYSICAL ROUTE ALIGNMENT (Phase 4.6.12)
# We use /api as prefix to flatten the paths requested by FE
router: APIRouter = APIRouter(prefix="/api", tags=["knowledge"])

# Backward compatibility aliases for old tests (GAP-012)
router.include_router(items_router, prefix="/knowledge-items")
router.include_router(items_router)
router.include_router(search_router)
router.include_router(crawling_router)
router.include_router(upload_router)


@router.get("/knowledge", response_model=KnowledgeItemsResponse)
@router.get("/knowledge/", response_model=KnowledgeItemsResponse)
async def list_knowledge_items_root(page: int = 1, per_page: int = 20) -> KnowledgeItemsResponse:
    """Satisfy front-end base /api/knowledge requests by delegating to items logic."""
    from ..services.knowledge.knowledge_item_service import KnowledgeItemService

    service = KnowledgeItemService(get_supabase_client())
    success, result_dict = await service.list_items(page=page, per_page=per_page)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to list knowledge items")

    return KnowledgeItemsResponse(
        items=result_dict.get("items", []),
        total=result_dict.get("total", 0),
        page=page,
        per_page=per_page
    )


@router.get("/knowledge/database/metrics", response_model=DatabaseMetricsResponse)
async def get_database_metrics() -> DatabaseMetricsResponse:
    from fastapi import HTTPException

    from ..config.logfire_config import safe_logfire_error
    from ..services.knowledge.database_metrics_service import DatabaseMetricsService

    try:
        service = DatabaseMetricsService(get_supabase_client())
        metrics = await service.get_metrics()
        return DatabaseMetricsResponse(**metrics)
    except Exception as e:
        safe_logfire_error(f"Failed to get database metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


__all__ = ["router", "active_crawl_tasks", "upload_document", "storage_service"]
