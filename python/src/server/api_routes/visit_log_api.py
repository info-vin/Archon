"""
Visit Log API Hardened - Secure management of physical visit records.
Lean implementation with full test compatibility.
"""

from fastapi import APIRouter, Depends, HTTPException

from src.server.services.visit_log_service import VisitLogService

from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/api/visit-logs", tags=["visit-logs"])

@router.get("")
async def list_visit_logs(lead_id: str | None = None, current_user: dict = Depends(get_current_user)):
    """Lists visit logs, optionally filtered by lead."""
    service = VisitLogService()
    success, res = await service.list_logs(lead_id=lead_id)
    if not success:
        raise HTTPException(status_code=500, detail=str(res))
    # Aligned: Service returns the data list directly in the second tuple element
    return res if isinstance(res, list) else []

@router.post("")
async def create_visit_log(log_data: dict, current_user: dict = Depends(get_current_user)):
    """Creates a new visit log."""
    service = VisitLogService()
    success, res = await service.create_log(log_data)
    if not success:
        raise HTTPException(status_code=400, detail=str(res))
    # Extract the first record from the inserted data
    data = res.get("data", []) if isinstance(res, dict) else res
    return data[0] if isinstance(data, list) and len(data) > 0 else {}

@router.get("/attendance/status")
async def get_attendance_status(current_user: dict = Depends(get_current_user)):
    """Fetches the current attendance status for the current user."""
    service = VisitLogService()
    success, res = await service.get_attendance_status(current_user["id"])
    if not success:
        raise HTTPException(status_code=500, detail=str(res))
    return res
