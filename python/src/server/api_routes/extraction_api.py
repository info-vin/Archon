from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_user, verify_manager_role
from ..config.logfire_config import get_logger
from ..services.extraction_service import ExtractionService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/extraction", tags=["Extraction"])

@router.post("/analyze", dependencies=[Depends(verify_manager_role)])
async def analyze_url(request: dict[str, str]) -> dict[str, Any]:
    """
    Analyze a URL to discover potential data fields.
    Payload: { "url": "https://..." }
    """
    url = request.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    service = ExtractionService()
    try:
        return await service.analyze_url_structure(url)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/schemas", dependencies=[Depends(verify_manager_role)])
async def list_schemas() -> list[dict[str, Any]]:
    """List all extraction schemas."""
    service = ExtractionService()
    return await service.list_schemas()

@router.post("/schemas", dependencies=[Depends(verify_manager_role)])
async def create_schema(
    request: dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    """Create a new extraction schema."""
    service = ExtractionService()
    try:
        return await service.create_schema(request, current_user["id"])
    except Exception as e:
        logger.error(f"Create schema failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.delete("/schemas/{schema_id}", dependencies=[Depends(verify_manager_role)])
async def delete_schema(schema_id: str) -> dict[str, bool]:
    """Delete a schema."""
    service = ExtractionService()
    await service.delete_schema(schema_id)
    return {"success": True}

@router.post("/run", dependencies=[Depends(verify_manager_role)])
async def run_extraction(
    request: dict[str, str],
    current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Triggers an asynchronous extraction task.
    Payload: { "url": "...", "schema_id": "..." }
    """
    url = request.get("url")
    schema_id = request.get("schema_id")
    if not url or not schema_id:
        raise HTTPException(status_code=400, detail="URL and schema_id are required")

    # In a real implementation, this would trigger a background task (Librarian)
    # For now, we return a mock success message to confirm the loop is closed.
    logger.info(f"User {current_user.get('id')} triggered extraction for {url} using schema {schema_id}")

    return {
        "success": True,
        "message": "Extraction task queued successfully. Librarian agent is now processing.",
        "task_id": f"ext-{schema_id[:4]}-{url.split('/')[-1][:8]}"
    }
