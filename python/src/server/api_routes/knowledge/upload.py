import asyncio
import json
import uuid

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from src.server.config.logfire_config import get_logger, safe_logfire_error

# TOP-LEVEL IMPORTS for Test Patching
from src.server.services.source_management_service import SourceManagementService
from src.server.services.storage.storage_services import DocumentStorageService
from src.server.utils.document_processing import extract_text_from_document
from src.server.utils.progress.progress_tracker import ProgressTracker

from ...auth.dependencies import get_current_user

# Domain State
from . import active_crawl_tasks

router = APIRouter()
logger = get_logger(__name__)


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    knowledge_type: str = Form("technical"),
    tags: str = Form("[]"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    current_user: dict = Depends(get_current_user),
):
    """Upload a document and process it into knowledge chunks."""
    try:
        tag_list = json.loads(tags)
        progress_id = str(uuid.uuid4())

        file_content = await file.read()
        file_metadata = {"filename": file.filename, "content_type": file.content_type, "size": len(file_content)}

        tracker = ProgressTracker(progress_id)
        await tracker.start({"status": "initializing", "progress": 0, "log": f"Starting upload for {file.filename}"})

        # Launch background task and store it for tracking (Physical Alignment with domain state)
        task = asyncio.create_task(
            background_upload(
                file_content=file_content,
                file_metadata=file_metadata,
                progress_id=progress_id,
                tags=tag_list,
                knowledge_type=knowledge_type,
                tracker=tracker,
            )
        )

        active_crawl_tasks[progress_id] = task

        return {"status": "success", "progress_id": progress_id, "message": "Upload started in background"}

    except Exception as e:
        safe_logfire_error(f"Upload initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


async def background_upload(
    file_content: bytes,
    file_metadata: dict,
    progress_id: str,
    tags: list[str],
    knowledge_type: str,
    tracker: ProgressTracker,
):
    """Background task for processing uploaded documents."""
    try:
        # Use top-level imported services
        storage = DocumentStorageService()
        source_manager = SourceManagementService()

        await tracker.update("extracting", 20, "Extracting text...")

        text = extract_text_from_document(file_content, file_metadata["filename"], file_metadata["content_type"])

        if not text:
            raise ValueError("No text could be extracted from the document.")

        await tracker.update("storing", 50, "Storing document...")

        # Simple implementation for seeding/upload
        source_id = f"upload-{file_metadata['filename']}-{uuid.uuid4().hex[:6]}"
        await source_manager.create_source_info(
            source_id=source_id,
            content_sample=text[:200],  # Required argument
            word_count=len(text.split()),
            knowledge_type=knowledge_type,
            tags=tags,
        )

        await storage.store_documents(documents=[{"source_id": source_id, "content": text, "metadata": file_metadata}])

        await tracker.complete({"log": "Upload successful!"})
    except Exception as e:
        safe_logfire_error(f"Background upload failed for {file_metadata.get('filename')}: {e}")
        await tracker.update("failed", 0, f"Error: {str(e)}")
    finally:
        if progress_id in active_crawl_tasks:
            del active_crawl_tasks[progress_id]
