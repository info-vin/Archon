
from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import TASK_READ_TEAM
from ..config.logfire_config import get_logger
from ..schemas.extraction import (
    AnalyzeUrlRequest,
    AnalyzeUrlResponse,
    DeleteSchemaResponse,
    ExtractionSchemaResponse,
    RunExtractionRequest,
    RunExtractionResponse,
    SchemaCreateRequest,
    SchemaUpdateRequest,
)
from ..services.extraction_service import ExtractionService

logger = get_logger(__name__)
router = APIRouter(prefix="/api/extraction", tags=["Extraction"])


@router.post("/analyze", dependencies=[Depends(requires_permission(TASK_READ_TEAM))], response_model=AnalyzeUrlResponse)
async def analyze_url(request: AnalyzeUrlRequest) -> AnalyzeUrlResponse:
    """
    Analyze a URL to discover potential data fields.
    """
    service = ExtractionService()
    try:
        result = await service.analyze_url_structure(request.url)
        return AnalyzeUrlResponse(**result)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/schemas", dependencies=[Depends(requires_permission(TASK_READ_TEAM))], response_model=list[ExtractionSchemaResponse])
async def list_schemas() -> list[ExtractionSchemaResponse]:
    """List all extraction schemas."""
    service = ExtractionService()
    results = await service.list_schemas()
    return [ExtractionSchemaResponse(**schema) for schema in results]


@router.get("/schemas/{schema_id}", dependencies=[Depends(requires_permission(TASK_READ_TEAM))], response_model=ExtractionSchemaResponse)
async def get_schema(schema_id: str) -> ExtractionSchemaResponse:
    """Get a single schema by ID."""
    service = ExtractionService()
    schema = await service.get_schema(schema_id)
    if not schema:
        raise HTTPException(status_code=404, detail="Schema not found")
    return ExtractionSchemaResponse(**schema)


@router.post("/schemas", dependencies=[Depends(requires_permission(TASK_READ_TEAM))], response_model=ExtractionSchemaResponse)
async def create_schema(request: SchemaCreateRequest, current_user: dict = Depends(get_current_user)) -> ExtractionSchemaResponse:
    """Create a new extraction schema."""
    service = ExtractionService()
    try:
        result = await service.create_schema(request.model_dump(exclude_unset=True), current_user["id"])
        return ExtractionSchemaResponse(**result)
    except Exception as e:
        logger.error(f"Create schema failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.patch("/schemas/{schema_id}", dependencies=[Depends(requires_permission(TASK_READ_TEAM))], response_model=ExtractionSchemaResponse)
async def update_schema(schema_id: str, request: SchemaUpdateRequest) -> ExtractionSchemaResponse:
    """Update an existing schema."""
    service = ExtractionService()
    try:
        result = await service.update_schema(schema_id, request.model_dump(exclude_unset=True))
        return ExtractionSchemaResponse(**result)
    except Exception as e:
        logger.error(f"Update schema failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/schemas/{schema_id}", dependencies=[Depends(requires_permission(TASK_READ_TEAM))], response_model=DeleteSchemaResponse)
async def delete_schema(schema_id: str) -> DeleteSchemaResponse:
    """Delete a schema."""
    service = ExtractionService()
    await service.delete_schema(schema_id)
    return DeleteSchemaResponse(success=True)


@router.post("/run", dependencies=[Depends(requires_permission(TASK_READ_TEAM))], response_model=RunExtractionResponse)
async def run_extraction(request: RunExtractionRequest, current_user: dict = Depends(get_current_user)) -> RunExtractionResponse:
    """
    Triggers an actual data extraction task.
    """
    service = ExtractionService()
    try:
        # Fulfills Phase 4.6.23: Functional Realization (No more Mock)
        result = await service.run_extraction(request.url, request.schema_id, current_user["id"])
        return RunExtractionResponse(**result)
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
