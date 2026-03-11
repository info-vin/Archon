from fastapi import APIRouter

# EXPORTS for test compatibility (GAP-012)
from ..services.storage_service import storage_service
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

router.include_router(items_router)
router.include_router(search_router)
router.include_router(crawling_router)
router.include_router(upload_router)

@router.get("/knowledge")
@router.get("/knowledge/")
async def list_knowledge_items_root():
    """Satisfy front-end base /api/knowledge requests."""
    return {"items": []}

@router.get("/knowledge/database/metrics")
async def get_database_metrics():
    from fastapi import HTTPException

    from ..config.logfire_config import safe_logfire_error
    from ..services.knowledge.database_metrics_service import DatabaseMetricsService
    try:
        service = DatabaseMetricsService(get_supabase_client())
        return await service.get_metrics()
    except Exception as e:
        safe_logfire_error(f"Failed to get database metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

__all__ = ["router", "active_crawl_tasks", "upload_document", "storage_service"]
