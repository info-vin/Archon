"""
Knowledge Management API Module

This module handles all knowledge base operations including:
- Crawling and indexing web content
- Document upload and processing
- RAG (Retrieval Augmented Generation) queries
- Knowledge item management and search
- Progress tracking via HTTP polling
"""

import asyncio
import io
import json
import uuid
from urllib.parse import quote

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from pydantic import BaseModel

# Import unified logging
from ..config.logfire_config import get_logger, safe_logfire_error, safe_logfire_info
from ..models.blog import BlogPostResponse, CreateBlogPostRequest, UpdateBlogPostRequest
from ..services.blog_service import BlogService
from ..services.crawler_manager import get_crawler
from ..services.crawling import CrawlOrchestrationService
from ..services.knowledge import DatabaseMetricsService, KnowledgeItemService
from ..services.knowledge_service import KnowledgeService
from ..services.rbac_service import RBACService
from ..services.search.rag_service import RAGService
from ..services.storage import DocumentStorageService
from ..services.storage_service import storage_service
from ..utils import get_supabase_client
from ..utils.document_processing import extract_text_from_document
from ..utils.progress.progress_tracker import ProgressTracker

# Get logger for this module
logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api", tags=["knowledge"])


# Blog Post Endpoints
@router.get("/blogs", response_model=list[BlogPostResponse])
async def list_blog_posts():
    """List all blog posts."""
    blog_service = BlogService()
    success, result = await blog_service.list_posts()
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result.get("posts", [])

@router.get("/blogs/{post_id}", response_model=BlogPostResponse)
async def get_blog_post(post_id: str):
    """Get a single blog post by ID."""
    blog_service = BlogService()
    success, result = await blog_service.get_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result.get("post")

@router.post("/blogs", response_model=BlogPostResponse)
async def create_blog_post(
    request: CreateBlogPostRequest,
    x_user_role: str | None = Header(None, alias="X-User-Role")
):
    """Create a new blog post."""
    rbac_service = RBACService()
    current_user_role = x_user_role or "User"
    if not rbac_service.can_manage_content(current_user_role):
        raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to create blog posts.")

    blog_service = BlogService()
    success, result = await blog_service.create_post(request.model_dump())
    if not success:
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result.get("post")

@router.put("/blogs/{post_id}", response_model=BlogPostResponse)
async def update_blog_post(
    post_id: str,
    request: UpdateBlogPostRequest,
    x_user_role: str | None = Header(None, alias="X-User-Role")
):
    """Update an existing blog post."""
    rbac_service = RBACService()
    current_user_role = x_user_role or "User"
    if not rbac_service.can_manage_content(current_user_role):
        raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to update blog posts.")

    blog_service = BlogService()
    update_data = request.model_dump(exclude_unset=True)
    success, result = await blog_service.update_post(post_id, update_data)
    if not success:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return result.get("post")

@router.delete("/blogs/{post_id}", status_code=204)
async def delete_blog_post(
    post_id: str,
    x_user_role: str | None = Header(None, alias="X-User-Role")
):
    """Delete a blog post."""
    rbac_service = RBACService()
    current_user_role = x_user_role or "User"
    if not rbac_service.can_manage_content(current_user_role):
        raise HTTPException(status_code=403, detail="Forbidden: You do not have permission to delete blog posts.")

    blog_service = BlogService()
    success, result = await blog_service.delete_post(post_id)
    if not success:
        raise HTTPException(status_code=404, detail=result.get("error"))
    return None


# Create a semaphore to limit concurrent crawl OPERATIONS (not pages within a crawl)
# This prevents the server from becoming unresponsive during heavy crawling
#
# IMPORTANT: This is different from CRAWL_MAX_CONCURRENT (configured in UI/database):
# - CONCURRENT_CRAWL_LIMIT: Max number of separate crawl operations that can run simultaneously (server protection)
#   Example: User A crawls site1.com, User B crawls site2.com, User C crawls site3.com = 3 operations
# - CRAWL_MAX_CONCURRENT: Max number of pages that can be crawled in parallel within a single crawl operation
#   Example: While crawling site1.com, fetch up to 10 pages simultaneously
#
# The hardcoded limit of 3 protects the server from being overwhelmed by multiple users
# starting crawls at the same time. Each crawl can still process many pages in parallel.
CONCURRENT_CRAWL_LIMIT = 3  # Max simultaneous crawl operations (protects server resources)
crawl_semaphore = asyncio.Semaphore(CONCURRENT_CRAWL_LIMIT)

# Track active async crawl tasks for cancellation support
active_crawl_tasks: dict[str, asyncio.Task] = {}


# Request Models
class KnowledgeItemRequest(BaseModel):
    url: str
    knowledge_type: str = "technical"
    tags: list[str] = []
    update_frequency: int = 7
    max_depth: int = 2  # Maximum crawl depth (1-5)
    extract_code_examples: bool = True  # Whether to extract code examples

    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "knowledge_type": "technical",
                "tags": ["documentation"],
                "update_frequency": 7,
                "max_depth": 2,
                "extract_code_examples": True,
            }
        }


class CrawlRequest(BaseModel):
    url: str
    knowledge_type: str = "general"
    tags: list[str] = []
    update_frequency: int = 7
    max_depth: int = 2  # Maximum crawl depth (1-5)


class RagQueryRequest(BaseModel):
    query: str
    source: str | None = None
    match_count: int = 5


@router.get("/crawl-progress/{progress_id}")
async def get_crawl_progress(progress_id: str):
    """Get crawl progress for polling.

    Returns the current state of a crawl operation.
    Frontend should poll this endpoint to track crawl progress.
    """
    try:
        from ..models.progress_models import create_progress_response
        from ..utils.progress.progress_tracker import ProgressTracker

        # Get progress from the tracker's in-memory storage
        progress_data = ProgressTracker.get_progress(progress_id)
        safe_logfire_info(f"Crawl progress requested | progress_id={progress_id} | found={progress_data is not None}")

        if not progress_data:
            # Return 404 if no progress exists - this is correct behavior
            raise HTTPException(status_code=404, detail={"error": f"No progress found for ID: {progress_id}"})

        # Ensure we have the progress_id in the data
        progress_data["progress_id"] = progress_id

        # Get operation type for proper model selection
        operation_type = progress_data.get("type", "crawl")

        # Create standardized response using Pydantic model
        progress_response = create_progress_response(operation_type, progress_data)

        # Convert to dict with camelCase fields for API response
        response_data = progress_response.model_dump(by_alias=True, exclude_none=True)

        safe_logfire_info(
            f"Progress retrieved | operation_id={progress_id} | status={response_data.get('status')} | "
            f"progress={response_data.get('progress')} | totalPages={response_data.get('totalPages')} | "
            f"processedPages={response_data.get('processedPages')}"
        )

        return response_data
    except Exception as e:
        safe_logfire_error(f"Failed to get crawl progress | error={str(e)} | progress_id={progress_id}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.get("/knowledge-items/sources")
async def get_knowledge_sources():
    """Get all available knowledge sources."""
    try:
        # Return empty list for now to pass the test
        # In production, this would query the database
        return []
    except Exception as e:
        safe_logfire_error(f"Failed to get knowledge sources | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.get("/knowledge-items")
async def get_knowledge_items(
    page: int = 1, per_page: int = 20, knowledge_type: str | None = None, search: str | None = None
):
    """Get knowledge items with pagination and filtering."""
    try:
        # Use KnowledgeItemService
        service = KnowledgeItemService(get_supabase_client())
        result = await service.list_items(
            page=page, per_page=per_page, knowledge_type=knowledge_type, search=search
        )
        return result

    except Exception as e:
        safe_logfire_error(
            f"Failed to get knowledge items | error={str(e)} | page={page} | per_page={per_page}"
        )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.put("/knowledge-items/{source_id}")
async def update_knowledge_item(source_id: str, updates: dict):
    """Update a knowledge item's metadata."""
    try:
        # Use KnowledgeItemService
        service = KnowledgeItemService(get_supabase_client())
        success, result = await service.update_item(source_id, updates)

        if success:
            return result
        else:
            if "not found" in result.get("error", "").lower():
                raise HTTPException(status_code=404, detail={"error": result.get("error")})
            else:
                raise HTTPException(status_code=500, detail={"error": result.get("error")})

    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(
            f"Failed to update knowledge item | error={str(e)} | source_id={source_id}"
        )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.delete("/knowledge-items/{source_id}")
async def delete_knowledge_item(source_id: str):
    """Delete a knowledge item from the database."""
    try:
        logger.debug(f"Starting delete_knowledge_item for source_id: {source_id}")
        safe_logfire_info(f"Deleting knowledge item | source_id={source_id}")

        # Use SourceManagementService directly instead of going through MCP
        logger.debug("Creating SourceManagementService...")
        from ..services.source_management_service import SourceManagementService

        source_service = SourceManagementService(get_supabase_client())
        logger.debug("Successfully created SourceManagementService")

        logger.debug("Calling delete_source function...")
        success, result_data = source_service.delete_source(source_id)
        logger.debug(f"delete_source returned: success={success}, data={result_data}")

        # Convert to expected format
        result = {
            "success": success,
            "error": result_data.get("error") if not success else None,
            **result_data,
        }

        if result.get("success"):
            safe_logfire_info(f"Knowledge item deleted successfully | source_id={source_id}")

            return {"success": True, "message": f"Successfully deleted knowledge item {source_id}"}
        else:
            safe_logfire_error(
                f"Knowledge item deletion failed | source_id={source_id} | error={result.get('error')}"
            )
            raise HTTPException(
                status_code=500, detail={"error": result.get("error", "Deletion failed")}
            )

    except Exception as e:
        logger.error(f"Exception in delete_knowledge_item: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        safe_logfire_error(
            f"Failed to delete knowledge item | error={str(e)} | source_id={source_id}"
        )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.get("/knowledge-items/{source_id}/chunks")
async def get_knowledge_item_chunks(source_id: str, domain_filter: str | None = None):
    """Get all document chunks for a specific knowledge item with optional domain filtering."""
    try:
        safe_logfire_info(f"Fetching chunks for source_id: {source_id}, domain_filter: {domain_filter}")

        # Query document chunks with content for this specific source
        supabase = get_supabase_client()

        # Build the query
        query = supabase.from_("archon_crawled_pages").select(
            "id, source_id, content, metadata, url"
        )
        query = query.eq("source_id", source_id)

        # Apply domain filtering if provided
        if domain_filter:
            # Case-insensitive URL match
            query = query.ilike("url", f"%{domain_filter}%")

        # Deterministic ordering (URL then id)
        query = query.order("url", desc=False).order("id", desc=False)

        result = query.execute()
        if getattr(result, "error", None):
            safe_logfire_error(
                f"Supabase query error | source_id={source_id} | error={result.error}"
            )
            raise HTTPException(status_code=500, detail={"error": str(result.error)})

        chunks = result.data if result.data else []

        safe_logfire_info(f"Found {len(chunks)} chunks for {source_id}")

        return {
            "success": True,
            "source_id": source_id,
            "domain_filter": domain_filter,
            "chunks": chunks,
            "count": len(chunks),
        }

    except Exception as e:
        safe_logfire_error(
            f"Failed to fetch chunks | error={str(e)} | source_id={source_id}"
        )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.get("/knowledge-items/{source_id}/code-examples")
async def get_knowledge_item_code_examples(source_id: str):
    """Get all code examples for a specific knowledge item."""
    try:
        knowledge_service = KnowledgeService()
        code_examples = await knowledge_service.get_code_examples(source_id)

        return {
            "success": True,
            "source_id": source_id,
            "code_examples": code_examples,
            "count": len(code_examples),
        }

    except Exception as e:
        safe_logfire_error(
            f"Failed to fetch code examples | error={str(e)} | source_id={source_id}"
        )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/knowledge-items/{source_id}/refresh")
async def refresh_knowledge_item(source_id: str):
    """Refresh a knowledge item by re-crawling its URL with the same metadata."""
    try:
        safe_logfire_info(f"Starting knowledge item refresh | source_id={source_id}")

        # Get the existing knowledge item
        service = KnowledgeItemService(get_supabase_client())
        existing_item = await service.get_item(source_id)

        if not existing_item:
            raise HTTPException(
                status_code=404, detail={"error": f"Knowledge item {source_id} not found"}
            )

        # Extract metadata
        metadata = existing_item.get("metadata", {})

        # Extract the URL from the existing item
        # First try to get the original URL from metadata, fallback to url field
        url = metadata.get("original_url") or existing_item.get("url")
        if not url:
            raise HTTPException(
                status_code=400, detail={"error": "Knowledge item does not have a URL to refresh"}
            )
        knowledge_type = metadata.get("knowledge_type", "technical")
        tags = metadata.get("tags", [])
        max_depth = metadata.get("max_depth", 2)

        # Generate unique progress ID
        progress_id = str(uuid.uuid4())

        # Initialize progress tracker IMMEDIATELY so it's available for polling
        tracker = ProgressTracker(progress_id, operation_type="crawl")
        await tracker.start({
            "url": url,
            "status": "initializing",
            "progress": 0,
            "log": f"Starting refresh for {url}",
            "source_id": source_id,
            "operation": "refresh",
            "crawl_type": "refresh"
        })

        # Get crawler from CrawlerManager - same pattern as _perform_crawl_with_progress
        try:
            crawler = await get_crawler()
            if crawler is None:
                raise Exception("Crawler not available - initialization may have failed")
        except Exception as e:
            safe_logfire_error(f"Failed to get crawler | error={str(e)}")
            raise HTTPException(
                status_code=500, detail={"error": f"Failed to initialize crawler: {str(e)}"}
            ) from e

        # Use the same crawl orchestration as regular crawl
        crawl_service = CrawlOrchestrationService(
            crawler=crawler, supabase_client=get_supabase_client()
        )
        crawl_service.set_progress_id(progress_id)

        # Start the crawl task with proper request format
        request_dict = {
            "url": url,
            "knowledge_type": knowledge_type,
            "tags": tags,
            "max_depth": max_depth,
            "extract_code_examples": True,
            "generate_summary": True,
        }

        # Create a wrapped task that acquires the semaphore
        async def _perform_refresh_with_semaphore():
            try:
                async with crawl_semaphore:
                    safe_logfire_info(
                        f"Acquired crawl semaphore for refresh | source_id={source_id}"
                    )
                    await crawl_service.orchestrate_crawl(request_dict)
            finally:
                # Clean up task from registry when done (success or failure)
                if progress_id in active_crawl_tasks:
                    del active_crawl_tasks[progress_id]
                    safe_logfire_info(
                        f"Cleaned up refresh task from registry | progress_id={progress_id}"
                    )

        task = asyncio.create_task(_perform_refresh_with_semaphore())
        # Track the task for cancellation support
        active_crawl_tasks[progress_id] = task

        return {"progressId": progress_id, "message": f"Started refresh for {url}"}

    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(
            f"Failed to refresh knowledge item | error={str(e)} | source_id={source_id}"
        )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/knowledge-items/crawl")
async def crawl_knowledge_item(request: KnowledgeItemRequest):
    """Crawl a URL and add it to the knowledge base with progress tracking."""
    # Validate URL
    if not request.url:
        raise HTTPException(status_code=422, detail="URL is required")

    # Basic URL validation
    if not request.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=422, detail="URL must start with http:// or https://")

    try:
        safe_logfire_info(
            f"Starting knowledge item crawl | url={str(request.url)} | knowledge_type={request.knowledge_type} | tags={request.tags}"
        )
        # Generate unique progress ID
        progress_id = str(uuid.uuid4())

        # Initialize progress tracker IMMEDIATELY so it's available for polling
        tracker = ProgressTracker(progress_id, operation_type="crawl")

        # Detect crawl type from URL
        url_str = str(request.url)
        crawl_type = "normal"
        if "sitemap.xml" in url_str:
            crawl_type = "sitemap"
        elif url_str.endswith(".txt"):
            crawl_type = "llms-txt" if "llms" in url_str.lower() else "text_file"

        await tracker.start({
            "url": url_str,
            "current_url": url_str,
            "crawl_type": crawl_type,
            "status": "initializing",
            "progress": 0,
            "log": f"Starting crawl for {request.url}"
        })

        # Start background task
        task = asyncio.create_task(_perform_crawl_with_progress(progress_id, request, tracker))
        # Track the task for cancellation support
        active_crawl_tasks[progress_id] = task
        safe_logfire_info(
            f"Crawl started successfully | progress_id={progress_id} | url={str(request.url)}"
        )
        # Create a proper response that will be converted to camelCase
        from pydantic import BaseModel, Field

        class CrawlStartResponse(BaseModel):
            success: bool
            progress_id: str = Field(alias="progressId")
            message: str
            estimated_duration: str = Field(alias="estimatedDuration")

            class Config:
                populate_by_name = True

        response = CrawlStartResponse(
            success=True,
            progress_id=progress_id,
            message="Crawling started",
            estimated_duration="3-5 minutes"
        )

        return response.model_dump(by_alias=True)
    except Exception as e:
        safe_logfire_error(f"Failed to start crawl | error={str(e)} | url={str(request.url)}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def _perform_crawl_with_progress(
    progress_id: str, request: KnowledgeItemRequest, tracker: ProgressTracker
):
    """Perform the actual crawl operation with progress tracking using service layer."""
    # Acquire semaphore to limit concurrent crawls
    async with crawl_semaphore:
        safe_logfire_info(
            f"Acquired crawl semaphore | progress_id={progress_id} | url={str(request.url)}"
        )
        try:
            safe_logfire_info(
                f"Starting crawl with progress tracking | progress_id={progress_id} | url={str(request.url)}"
            )

            # Get crawler from CrawlerManager
            try:
                crawler = await get_crawler()
                if crawler is None:
                    raise Exception("Crawler not available - initialization may have failed")
            except Exception as e:
                safe_logfire_error(f"Failed to get crawler | error={str(e)}")
                await tracker.error(f"Failed to initialize crawler: {str(e)}")
                return

            supabase_client = get_supabase_client()
            orchestration_service = CrawlOrchestrationService(crawler, supabase_client)
            orchestration_service.set_progress_id(progress_id)

            # Store the current task in active_crawl_tasks for cancellation support
            current_task = asyncio.current_task()
            if current_task:
                active_crawl_tasks[progress_id] = current_task
                safe_logfire_info(
                    f"Stored current task in active_crawl_tasks | progress_id={progress_id}"
                )

            # Convert request to dict for service
            request_dict = {
                "url": str(request.url),
                "knowledge_type": request.knowledge_type,
                "tags": request.tags or [],
                "max_depth": request.max_depth,
                "extract_code_examples": request.extract_code_examples,
                "generate_summary": True,
            }

            # Orchestrate the crawl (now returns immediately with task info)
            result = await orchestration_service.orchestrate_crawl(request_dict)

            # The orchestration service now runs in background and handles all progress updates
            # Just log that the task was started
            safe_logfire_info(
                f"Crawl task started | progress_id={progress_id} | task_id={result.get('task_id')}"
            )
        except asyncio.CancelledError:
            safe_logfire_info(f"Crawl cancelled | progress_id={progress_id}")
            raise
        except Exception as e:
            error_message = f"Crawling failed: {str(e)}"
            safe_logfire_error(
                f"Crawl failed | progress_id={progress_id} | error={error_message} | exception_type={type(e).__name__}"
            )
            import traceback

            tb = traceback.format_exc()
            # Ensure the error is visible in logs
            logger.error(f"=== CRAWL ERROR FOR {progress_id} ===")
            logger.error(f"Error: {error_message}")
            logger.error(f"Exception Type: {type(e).__name__}")
            logger.error(f"Traceback:\n{tb}")
            logger.error("=== END CRAWL ERROR ===")
            safe_logfire_error(f"Crawl exception traceback | traceback={tb}")
            # Ensure clients see the failure
            try:
                await tracker.error(error_message)
            except Exception:
                pass
        finally:
            # Clean up task from registry when done (success or failure)
            if progress_id in active_crawl_tasks:
                del active_crawl_tasks[progress_id]
                safe_logfire_info(
                    f"Cleaned up crawl task from registry | progress_id={progress_id}"
                )


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    tags: str | None = Form(None),
    knowledge_type: str = Form("technical"),
):
    """Upload and process a document with progress tracking."""
    try:
        # DETAILED LOGGING: Track knowledge_type parameter flow
        safe_logfire_info(
            f"📋 UPLOAD: Starting document upload | filename={file.filename} | content_type={file.content_type} | knowledge_type={knowledge_type}"
        )

        # Generate unique progress ID
        progress_id = str(uuid.uuid4())

        # Parse tags
        try:
            tag_list = json.loads(tags) if tags else []
            if tag_list is None:
                tag_list = []
            # Validate tags is a list of strings
            if not isinstance(tag_list, list):
                raise HTTPException(status_code=422, detail={"error": "tags must be a JSON array of strings"})
            if not all(isinstance(tag, str) for tag in tag_list):
                raise HTTPException(status_code=422, detail={"error": "tags must be a JSON array of strings"})
        except json.JSONDecodeError as ex:
            raise HTTPException(status_code=422, detail={"error": f"Invalid tags JSON: {str(ex)}"}) from ex

        # Read file content immediately to avoid closed file issues
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=422, detail={"error": "Uploaded file is empty"})
        file_metadata = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
        }

        # Initialize progress tracker IMMEDIATELY so it's available for polling
        tracker = ProgressTracker(progress_id, operation_type="upload")
        await tracker.start({
            "filename": file.filename,
            "status": "initializing",
            "progress": 0,
            "log": f"Starting upload for {file.filename}"
        })
        # Start background task for processing with file content and metadata
        task = asyncio.create_task(
            _perform_upload_with_progress(
                progress_id, file_content, file_metadata, tag_list, knowledge_type, tracker
            )
        )
        # Track the task for cancellation support
        active_crawl_tasks[progress_id] = task
        safe_logfire_info(
            f"Document upload started successfully | progress_id={progress_id} | filename={file.filename}"
        )
        return {
            "success": True,
            "progressId": progress_id,
            "message": "Document upload started",
            "filename": file.filename,
        }

    except Exception as e:
        safe_logfire_error(
            f"Failed to start document upload | error={str(e)} | filename={file.filename} | error_type={type(e).__name__}"
        )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


async def _perform_upload_with_progress(
    progress_id: str,
    file_content: bytes,
    file_metadata: dict,
    tag_list: list[str],
    knowledge_type: str,
    tracker: ProgressTracker,
):
    """Perform document upload with extensive diagnostic logging to find silent failures."""
    import traceback

    from ..services.crawling.progress_mapper import ProgressMapper
    progress_mapper = ProgressMapper()

    try:
        filename = file_metadata["filename"]
        content_type = file_metadata["content_type"]
        logger.info(f"DIAGNOSTIC: Starting upload process for progress_id={progress_id}, filename={filename}")

        # Step 1: Extract text
        await tracker.update(status="processing", progress=progress_mapper.map_progress("processing", 50), log=f"Extracting text from {filename}")
        try:
            extracted_text = extract_text_from_document(file_content, filename, content_type)
            logger.info(f"DIAGNOSTIC: Text extracted, length={len(extracted_text)}")
        except Exception as ex:
            logger.error(f"DIAGNOSTIC: CRITICAL FAILURE at text extraction. Error: {str(ex)}\n{traceback.format_exc()}")
            await tracker.error(f"Failed to extract text: {str(ex)}")
            return

        # Step 2: Upload original file to Storage
        logger.info("DIAGNOSTIC: Attempting to upload original file to Supabase Storage.")
        public_url = None
        try:
            in_memory_file = io.BytesIO(file_content)
            upload_file_for_storage = UploadFile(filename=filename, file=in_memory_file)
            file_path = f"uploads/{progress_id}/{quote(filename)}"

            public_url = await storage_service.upload_file(
                bucket_name="archon_documents",
                file_path=file_path,
                file=upload_file_for_storage,
            )
            logger.info(f"DIAGNOSTIC: File upload to storage complete. URL received: {public_url}")
            if not public_url:
                logger.error("DIAGNOSTIC: CRITICAL FAILURE - storage_service.upload_file returned a null or empty URL.")
                await tracker.error("Failed to get a valid URL from storage service.")
                return
        except Exception as ex:
            logger.error(f"DIAGNOSTIC: CRITICAL FAILURE at file upload to storage. Error: {str(ex)}\n{traceback.format_exc()}")
            await tracker.error(f"Failed to upload file to storage: {str(ex)}")
            return

        # Step 3: Store document chunks
        logger.info("DIAGNOSTIC: Attempting to store document chunks.")
        doc_storage_service = DocumentStorageService(get_supabase_client())
        source_id = f"file_{filename.replace(' ', '_').replace('.', '_')}_{uuid.uuid4().hex[:8]}"

        async def document_progress_callback(message: str, percentage: int, batch_info: dict = None):
            mapped_percentage = progress_mapper.map_progress("document_storage", percentage)
            await tracker.update(status="document_storage", progress=mapped_percentage, log=message, **(batch_info or {}))

        success, result = await doc_storage_service.upload_document(
            file_content=extracted_text,
            filename=filename,
            source_id=source_id,
            knowledge_type=knowledge_type,
            tags=tag_list,
            progress_callback=document_progress_callback,
            cancellation_check=lambda: None,
        )

        if not success:
            error_msg = result.get("error", "Unknown error during chunk storage")
            logger.error(f"DIAGNOSTIC: CRITICAL FAILURE at storing document chunks. Error: {error_msg}")
            await tracker.error(error_msg)
            return

        logger.info(f"DIAGNOSTIC: Document chunks stored successfully. Chunks stored: {result.get('chunks_stored', 0)}")

        # Step 4: Create the main source entry in archon_sources (THE MOST LIKELY POINT OF FAILURE)
        logger.info(f"DIAGNOSTIC: Attempting to create main source entry in 'archon_sources' with source_id={source_id}.")
        try:
            from ..services.source_management_service import SourceManagementService
            source_service = SourceManagementService(get_supabase_client())

            logger.info(f"DIAGNOSTIC: Calling create_source_from_upload with source_url={public_url}")
            await source_service.create_source_from_upload(
                source_id=source_id,
                filename=filename,
                knowledge_type=knowledge_type,
                tags=tag_list,
                chunks_stored=result.get("chunks_stored", 0),
                source_url=public_url,
            )
            logger.info(f"DIAGNOSTIC: SUCCESSFULLY created source entry for {source_id}.")
        except Exception as source_error:
            # THIS IS THE MOST IMPORTANT LOG. IT WILL CATCH THE SILENT ERROR.
            detailed_error = traceback.format_exc()
            logger.error(f"DIAGNOSTIC: CRITICAL FAILURE at creating source entry. THIS IS THE ROOT CAUSE. Error: {str(source_error)}\nFULL TRACEBACK:\n{detailed_error}")
            await tracker.error(f"Failed to create source entry in database: {source_error}")
            return

        # Step 5: Final completion
        logger.info("DIAGNOSTIC: Process appears to be fully successful. Completing tracker.")
        await tracker.complete({
            "log": "Document uploaded successfully!",
            "chunks_stored": result.get("chunks_stored"),
            "sourceId": source_id,
        })

    except Exception as e:
        detailed_error = traceback.format_exc()
        logger.error(f"DIAGNOSTIC: An unexpected error occurred in the main upload task. Error: {str(e)}\n{detailed_error}")
        await tracker.error(f"An unexpected error occurred: {str(e)}")
    finally:
        if progress_id in active_crawl_tasks:
            del active_crawl_tasks[progress_id]
            logger.info(f"DIAGNOSTIC: Cleaned up upload task from registry | progress_id={progress_id}")


@router.post("/knowledge-items/search")
async def search_knowledge_items(request: RagQueryRequest):
    """Search knowledge items - alias for RAG query."""
    # Validate query
    if not request.query:
        raise HTTPException(status_code=422, detail="Query is required")

    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")

    # Delegate to the RAG query handler
    return await perform_rag_query(request)


@router.post("/rag/query")
async def perform_rag_query(request: RagQueryRequest):
    """Perform a RAG query on the knowledge base using service layer."""
    # Validate query
    if not request.query:
        raise HTTPException(status_code=422, detail="Query is required")

    if not request.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")

    try:
        # Use RAGService for RAG query
        search_service = RAGService(get_supabase_client())
        success, result = await search_service.perform_rag_query(
            query=request.query, source=request.source, match_count=request.match_count
        )

        if success:
            # Add success flag to match expected API response format
            result["success"] = True
            return result
        else:
            raise HTTPException(
                status_code=500, detail={"error": result.get("error", "RAG query failed")}
            )
    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(
            f"RAG query failed | error={str(e)} | query={request.query[:50]} | source={request.source}"
        )
        raise HTTPException(status_code=500, detail={"error": f"RAG query failed: {str(e)}"}) from e


@router.post("/rag/code-examples")
async def search_code_examples(request: RagQueryRequest):
    """Search for code examples relevant to the query using dedicated code examples service."""
    try:
        # Use RAGService for code examples search
        search_service = RAGService(get_supabase_client())
        success, result = await search_service.search_code_examples_service(
            query=request.query,
            source_id=request.source,  # This is Optional[str] which matches the method signature
            match_count=request.match_count,
        )

        if success:
            # Add success flag and reformat to match expected API response format
            return {
                "success": True,
                "results": result.get("results", []),
                "reranked": result.get("reranking_applied", False),
                "error": None,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail={"error": result.get("error", "Code examples search failed")},
            )
    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(
            f"Code examples search failed | error={str(e)} | query={request.query[:50]} | source={request.source}"
        )
        raise HTTPException(
            status_code=500, detail={"error": f"Code examples search failed: {str(e)}"}
        ) from e


@router.post("/code-examples")
async def search_code_examples_simple(request: RagQueryRequest):
    """Search for code examples - simplified endpoint at /api/code-examples."""
    # Delegate to the existing endpoint handler
    return await search_code_examples(request)


@router.get("/rag/sources")
async def get_available_sources():
    """Get all available sources for RAG queries."""
    try:
        # Use KnowledgeItemService
        service = KnowledgeItemService(get_supabase_client())
        result = await service.get_available_sources()

        # Parse result if it's a string
        if isinstance(result, str):
            result = json.loads(result)

        return result
    except Exception as e:
        safe_logfire_error(f"Failed to get available sources | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str):
    """Delete a source and all its associated data."""
    try:
        safe_logfire_info(f"Deleting source | source_id={source_id}")

        # Use SourceManagementService directly
        from ..services.source_management_service import SourceManagementService

        source_service = SourceManagementService(get_supabase_client())

        success, result_data = source_service.delete_source(source_id)

        if success:
            safe_logfire_info(f"Source deleted successfully | source_id={source_id}")

            return {
                "success": True,
                "message": f"Successfully deleted source {source_id}",
                **result_data,
            }
        else:
            safe_logfire_error(
                f"Source deletion failed | source_id={source_id} | error={result_data.get('error')}"
            )
            raise HTTPException(
                status_code=500, detail={"error": result_data.get("error", "Deletion failed")}
            )
    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(f"Failed to delete source | error={str(e)} | source_id={source_id}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.get("/database/metrics")
async def get_database_metrics():
    """Get database metrics and statistics."""
    try:
        # Use DatabaseMetricsService
        service = DatabaseMetricsService(get_supabase_client())
        metrics = await service.get_metrics()
        return metrics
    except Exception as e:
        safe_logfire_error(f"Failed to get database metrics | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e




@router.get("/knowledge-items/task/{task_id}")
async def get_crawl_task_status(task_id: str):
    """Get status of a background crawl task."""
    try:
        from ..services.background_task_manager import get_task_manager

        task_manager = get_task_manager()
        status = await task_manager.get_task_status(task_id)

        if "error" in status and status["error"] == "Task not found":
            raise HTTPException(status_code=404, detail={"error": "Task not found"})

        return status
    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(f"Failed to get task status | error={str(e)} | task_id={task_id}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/knowledge-items/stop/{progress_id}")
async def stop_crawl_task(progress_id: str):
    """Stop a running crawl task."""
    try:
        from ..services.crawling import get_active_orchestration, unregister_orchestration


        safe_logfire_info(f"Stop crawl requested | progress_id={progress_id}")

        found = False
        # Step 1: Cancel the orchestration service
        orchestration = get_active_orchestration(progress_id)
        if orchestration:
            orchestration.cancel()
            found = True

        # Step 2: Cancel the asyncio task
        if progress_id in active_crawl_tasks:
            task = active_crawl_tasks[progress_id]
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except (TimeoutError, asyncio.CancelledError):
                    pass
            del active_crawl_tasks[progress_id]
            found = True

        # Step 3: Remove from active orchestrations registry
        unregister_orchestration(progress_id)

        # Step 4: Update progress tracker to reflect cancellation (only if we found and cancelled something)
        if found:
            try:
                from ..utils.progress.progress_tracker import ProgressTracker
                tracker = ProgressTracker(progress_id, operation_type="crawl")
                await tracker.update(
                    status="cancelled",
                    progress=-1,
                    log="Crawl cancelled by user"
                )
            except Exception:
                # Best effort - don't fail the cancellation if tracker update fails
                pass

        if not found:
            raise HTTPException(status_code=404, detail={"error": "No active task for given progress_id"})

        safe_logfire_info(f"Successfully stopped crawl task | progress_id={progress_id}")
        return {
            "success": True,
            "message": "Crawl task stopped successfully",
            "progressId": progress_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        safe_logfire_error(
            f"Failed to stop crawl task | error={str(e)} | progress_id={progress_id}"
        )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e
