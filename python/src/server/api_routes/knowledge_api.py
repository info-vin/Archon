"""
Knowledge API - Facade Layer
Modularized into src.server.api_routes.knowledge/ for better maintainability.
Provides backward compatibility for existing imports and test patches.
"""

from typing import Any
import asyncio
from fastapi import APIRouter

# 1. TOP-LEVEL IMPORTS (Satisfy E402)
from src.server.api_routes.knowledge.schemas import (
    KnowledgeItemRequest,
    CrawlRequest,
    RagQueryRequest,
    CrawlStartResponse
)
from src.server.api_routes.knowledge.items import router as items_router
from src.server.api_routes.knowledge.search import router as search_router
from src.server.api_routes.knowledge.crawling import (
    router as crawling_router,
    active_crawl_tasks
)
from src.server.api_routes.knowledge.upload import (
    router as upload_router,
    upload_document,
    _perform_upload_with_progress
)

# PHYSICAL ANCHORS for tests
from src.server.services.storage_service import storage_service
from src.server.services.rbac_service import RBACService
from src.server.services.storage.storage_services import DocumentStorageService
from src.server.services.source_management_service import SourceManagementService
from src.server.utils.progress.progress_tracker import ProgressTracker
from src.server.utils.document_processing import extract_text_from_document
from src.server.utils import get_supabase_client

# 2. DEFINITIONS
router: APIRouter = APIRouter(prefix="/api", tags=["knowledge"])

router.include_router(items_router)
router.include_router(search_router)
router.include_router(crawling_router)
router.include_router(upload_router)

# Metadata and Metrics
@router.get("/database/metrics")
async def get_database_metrics():
    """Get metrics about the knowledge base database."""
    from typing import cast
    from fastapi import HTTPException
    from src.server.config.logfire_config import safe_logfire_error
    from src.server.services.knowledge.database_metrics_service import DatabaseMetricsService
    try:
        service = DatabaseMetricsService(get_supabase_client())
        success, metrics = await service.get_metrics()
        if not success:
            err_msg = str(cast(dict, metrics).get("error", "Unknown metrics error"))
            raise HTTPException(status_code=500, detail=err_msg)
        return metrics
    except Exception as e:
        safe_logfire_error(f"Failed to get database metrics | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e

__all__ = [
    "router", "KnowledgeItemRequest", "CrawlRequest", "RagQueryRequest", "CrawlStartResponse",
    "upload_document", "_perform_upload_with_progress",
    "storage_service", "RBACService", "DocumentStorageService", "SourceManagementService", "ProgressTracker", 
    "extract_text_from_document", "get_supabase_client", "active_crawl_tasks"
]
