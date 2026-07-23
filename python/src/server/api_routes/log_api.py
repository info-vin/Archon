"""
Log API Hardened - Secure auditing of system and agent activities.
Ensures operational logs are only accessible to authorized personnel.
"""


from fastapi import APIRouter, Depends, status

from src.server.services.log_service import log_service

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import TASK_READ_TEAM
from ..schemas.logs import RecordGeminiLogResponse

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("/record-gemini-log", status_code=status.HTTP_201_CREATED, response_model=RecordGeminiLogResponse)
async def record_gemini_log(log_data: dict, current_user: dict = Depends(get_current_user)) -> RecordGeminiLogResponse:
    """Logs an AI interaction. Available to all authenticated users/agents."""
    return await log_service.record_interaction(str(current_user.get("id")), log_data)


@router.get("/alerts")
async def get_system_alerts(current_user: dict = Depends(requires_permission(TASK_READ_TEAM))):
    """Charlie checks for system alerts and operational errors. Requires Manager visibility."""
    return await log_service.get_active_alerts()
