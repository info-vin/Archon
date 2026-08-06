

from fastapi import APIRouter, Depends, HTTPException

from src.server.models.auth_models import UserProfileDTO

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import TASK_READ_TEAM
from ..config.logfire_config import get_logger
from ..services.extraction_service import (
    ExtractionResultDTO,
    ExtractionService,
    SchemaCreateDTO,
    SchemaResponseDTO,
    SchemaUpdateDTO,
    StructureAnalysisResultDTO,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/extraction", tags=["Extraction"])


@router.post("/analyze", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def analyze_url(request: dict[str, str]) -> StructureAnalysisResultDTO:
    """
    Analyze a URL to discover potential data fields.
    Payload: { "url": "https://..." } # 合法
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


@router.get("/schemas", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def list_schemas() -> list[SchemaResponseDTO]:
    """List all extraction schemas."""
    service = ExtractionService()
    return await service.list_schemas()


@router.get("/schemas/{schema_id}", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_schema(schema_id: str) -> SchemaResponseDTO:
    """Get a single schema by ID."""
    service = ExtractionService()
    schema = await service.get_schema(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return schema


@router.post("/schemas", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def create_schema(request: SchemaCreateDTO, current_user: UserProfileDTO = Depends(get_current_user)) -> SchemaResponseDTO:
    """Create a new extraction schema."""
    service = ExtractionService()
    try:
        return await service.create_schema(request, current_user.id)
    except Exception as e:
        logger.error(f"Create schema failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/schemas/{schema_id}", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def update_schema(schema_id: str, request: SchemaUpdateDTO) -> SchemaResponseDTO:
    """Update an existing schema."""
    service = ExtractionService()
    try:
        return await service.update_schema(schema_id, request)
    except Exception as e:
        logger.error(f"Update schema failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/schemas/{schema_id}", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def delete_schema(schema_id: str) -> dict[str, bool]:
    """Delete a schema."""
    service = ExtractionService()
    await service.delete_schema(schema_id)
    return {"success": True}


@router.post("/run", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def run_extraction(request: dict[str, str], current_user: UserProfileDTO = Depends(get_current_user)) -> ExtractionResultDTO:
    """
    Triggers an actual data extraction task.
    Payload: { "url": "...", "schema_id": "..." }
    """
    url = request.get("url")
    schema_id = request.get("schema_id")
    if not url or not schema_id:
        raise HTTPException(status_code=400, detail="URL and schema_id are required")

    service = ExtractionService()
    try:
        # Fulfills Phase 4.6.23: Functional Realization (No more Mock)
        return await service.run_extraction(url, schema_id, current_user.id)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
