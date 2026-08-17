"""
Visit Log API Hardened - Secure management of physical visit records.
Lean implementation with full test compatibility and GAP-009 Realization.
"""

from typing import cast

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.server.models.auth_models import UserProfileDTO
from src.server.schemas.visit_logs import AttendanceStatusResponse, VisitLogResponse
from src.server.services.visit_log_service import visit_log_service

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import TASK_CREATE, TASK_READ_TEAM

router = APIRouter(prefix="/api/visit-logs", tags=["visit-logs"])


@router.get("", response_model=list[VisitLogResponse])
async def list_visit_logs(
    lead_id: str | None = None, current_user: UserProfileDTO = Depends(requires_permission(TASK_READ_TEAM))
) -> list[VisitLogResponse]:
    """Lists visit logs, optionally filtered by lead. Restricted to Manager/Admin."""
    success, res = await visit_log_service.list_logs(lead_id=lead_id)
    if not success:
        raise HTTPException(status_code=500, detail=str(res))
    return cast(list[VisitLogResponse], res if isinstance(res, list) else [])


@router.post("", response_model=VisitLogResponse, status_code=201)
async def create_visit_log(
    company_name: str | None = Form(None),
    customer_id: str | None = Form(None),
    lead_id: str | None = Form(None),
    latitude: float | None = Form(None),
    longitude: float | None = Form(None),
    location_address: str | None = Form(None),
    audio_file: UploadFile | None = File(None),
    current_user: UserProfileDTO = Depends(requires_permission(TASK_CREATE)),
) -> VisitLogResponse:
    """
    Creates a new visit log from voice or text (GAP-009).
    Delegates Voice-to-Task logic to VisitLogService (04-14 Aligned).
    """
    # Physical identity injection
    log_data = {
        "user_id": current_user.id,
        "company_name": company_name,
        "customer_id": customer_id,
        "lead_id": lead_id,
        "latitude": latitude,
        "longitude": longitude,
        "location_address": location_address or company_name,
    }

    from src.server.services.visit_log_service import VisitLogDataDict
    clean_data: VisitLogDataDict = cast(VisitLogDataDict, {k: v for k, v in log_data.items() if v is not None})

    # Pass everything to Service layer for atomic realization
    success, res = await visit_log_service.create_log(data=clean_data, audio_file=audio_file)

    if not success:
        raise HTTPException(status_code=400, detail=str(res))

    return cast(VisitLogResponse, res)


@router.get("/attendance/status", response_model=AttendanceStatusResponse)
async def get_attendance_status(current_user: UserProfileDTO = Depends(get_current_user)) -> AttendanceStatusResponse:
    """Fetches the current attendance status for the current user."""
    success, res = await visit_log_service.get_attendance_status(current_user.id)
    if not success:
        raise HTTPException(status_code=500, detail=str(res))
    return cast(AttendanceStatusResponse, res)
