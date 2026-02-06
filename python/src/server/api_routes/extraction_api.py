from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.extraction_service import ExtractionService
from ..services.rbac_service import RBACService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/extraction", tags=["Extraction"])

async def require_manager(x_user_role: str | None = Header(None, alias="X-User-Role")):
    """Dependency to ensure user is at least a Manager."""
    rbac = RBACService()
    if not x_user_role or not rbac.can_manage_content(x_user_role):
        raise HTTPException(status_code=403, detail="Access Denied: Requires Manager privileges.")
    return x_user_role

@router.post("/analyze", dependencies=[Depends(require_manager)])
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

@router.get("/schemas", dependencies=[Depends(require_manager)])
async def list_schemas() -> list[dict[str, Any]]:
    """List all extraction schemas."""
    service = ExtractionService()
    return await service.list_schemas()

@router.post("/schemas", dependencies=[Depends(require_manager)])
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

@router.delete("/schemas/{schema_id}", dependencies=[Depends(require_manager)])
async def delete_schema(schema_id: str) -> dict[str, bool]:
    """Delete a schema."""
    service = ExtractionService()
    await service.delete_schema(schema_id)
    return {"success": True}
