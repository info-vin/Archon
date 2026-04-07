import asyncio
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException

from src.server.api_routes.knowledge.schemas import CrawlRequest
from src.server.config.logfire_config import safe_logfire_error, safe_logfire_info
from src.server.services.knowledge.knowledge_item_service import KnowledgeItemService
from src.server.utils import get_supabase_client
from src.server.utils.progress.progress_tracker import ProgressTracker

from ...auth.dependencies import requires_permission
from ...auth.permissions import TASK_CREATE

# CENTRAL TASK REGISTRY - Defined here to allow PEP8 compliant top-level imports in Facade
active_crawl_tasks: dict[str, asyncio.Task] = {}

router: APIRouter = APIRouter()


@router.get("/crawl-progress/{progress_id}")
async def get_crawl_progress(progress_id: str):
    """Get the current progress of a crawl or refresh operation. Public within system."""
    try:
        tracker = ProgressTracker(progress_id)
        status = tracker.get_state()
        if not status:
            raise HTTPException(status_code=404, detail="Progress ID not found")
        return status
    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(f"Failed to get crawl progress {progress_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/knowledge-items/stop/{progress_id}")
async def stop_crawl_operation(
    progress_id: str, current_user: dict = Depends(requires_permission(TASK_CREATE))
):
    """Stop an active crawl or refresh operation. Requires TASK_CREATE."""
    from src.server.services.crawling import unregister_orchestration

    try:
        safe_logfire_info(f"Stop crawl requested | progress_id={progress_id}")
        if progress_id in active_crawl_tasks:
            task = active_crawl_tasks[progress_id]
            task.cancel()
            del active_crawl_tasks[progress_id]

            tracker = ProgressTracker(progress_id)
            await tracker.update(status="stopped", progress=100, log="Operation stopped by user")
            return {"success": True, "message": f"Operation {progress_id} stopped"}
        else:
            unregister_orchestration(progress_id)
            return {"success": True, "message": f"Stop signal sent to {progress_id}"}
    except Exception as e:
        safe_logfire_error(f"Failed to stop operation {progress_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/knowledge-items/{source_id}/refresh")
async def refresh_knowledge_item(
    source_id: str,
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    current_user: dict = Depends(requires_permission(TASK_CREATE)),
):
    """Refresh an existing knowledge item by re-crawling its source. Requires TASK_CREATE."""
    # LATE IMPORT to share the same physical registry with other modules
    from server.services.rbac_service import RBACService

    try:
        service = KnowledgeItemService(get_supabase_client())
        success, res = await service.get_item(source_id)

        if not success or not res.get("item"):
            raise HTTPException(status_code=404, detail=f"Knowledge item {source_id} not found")

        existing_item = res["item"]
        metadata = existing_item.get("metadata", {})
        url = existing_item.get("source_url")

        if not url:
            raise HTTPException(status_code=400, detail="Item has no source URL to refresh")

        rbac_service = RBACService()
        constraints = rbac_service.get_crawler_constraints(x_user_role)
        max_depth = min(metadata.get("max_depth", 2), constraints["max_depth"])

        progress_id = str(uuid.uuid4())
        tracker = ProgressTracker(progress_id)
        await tracker.update(
            status="initializing",
            progress=0,
            log=f"Starting refresh for {url} (Role: {x_user_role or 'unknown'})",
            source_id=source_id,
            operation="refresh",
            crawl_type="refresh",
        )

        from src.server.services.crawler_manager import get_crawler
        from src.server.services.crawling import CrawlOrchestrationService

        crawler = get_crawler()
        crawl_service = CrawlOrchestrationService(crawler=crawler, supabase_client=get_supabase_client())
        crawl_service.set_progress_id(progress_id)

        request_dict = {
            "url": url,
            "knowledge_type": metadata.get("knowledge_type", "technical"),
            "tags": metadata.get("tags", []),
            "max_depth": max_depth,
            "is_refresh": True,
            "source_id": source_id,
        }

        task = asyncio.create_task(crawl_service.orchestrate_crawl(request_dict))
        active_crawl_tasks[progress_id] = task
        safe_logfire_info(f"Refresh task created | progress_id={progress_id} | url={url}")

        return {"success": True, "progressId": progress_id, "message": "Refresh started"}

    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(f"Failed to refresh item {source_id} | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/knowledge-items/crawl")
async def crawl_knowledge_item(
    request: CrawlRequest,
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    current_user: dict = Depends(requires_permission(TASK_CREATE)),
):
    """Start a new web crawl to populate the knowledge base. Requires TASK_CREATE."""
    # LATE IMPORT to share the same physical registry with other modules
    from server.services.rbac_service import RBACService

    try:
        rbac_service = RBACService()
        constraints = rbac_service.get_crawler_constraints(x_user_role)
        max_depth = min(request.max_depth, constraints["max_depth"])

        progress_id = str(uuid.uuid4())
        tracker = ProgressTracker(progress_id)
        await tracker.update(
            status="initializing",
            progress=0,
            log=f"Initializing crawl for {request.url}...",
            operation="crawl",
            crawl_type="new",
        )

        from src.server.services.crawler_manager import get_crawler
        from src.server.services.crawling import CrawlOrchestrationService

        crawler = get_crawler()
        orchestration_service = CrawlOrchestrationService(crawler, get_supabase_client())
        orchestration_service.set_progress_id(progress_id)

        request_dict = {
            "url": str(request.url),
            "knowledge_type": request.knowledge_type,
            "tags": request.tags,
            "max_depth": max_depth,
            "max_concurrent": constraints.get("max_concurrent", 3),
        }

        task = asyncio.create_task(orchestration_service.orchestrate_crawl(request_dict))
        active_crawl_tasks[progress_id] = task

        return {
            "success": True,
            "progressId": progress_id,
            "message": "Crawling started",
            "estimatedDuration": "3-5 minutes",
        }
    except Exception as e:
        safe_logfire_error(f"Failed to start crawl | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
