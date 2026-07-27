"""
Log API Hardened - Secure auditing of system and agent activities.
Ensures operational logs are only accessible to authorized personnel.
"""


from typing import Any, cast

from fastapi import APIRouter, Depends, status

from src.server.models.auth_models import UserProfileDTO
from src.server.services.log_service import LogDataDTO, log_service

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import TASK_READ_TEAM
from ..schemas.agent_outputs import LogEntry, RecordGeminiLogResponse

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.post("/record-gemini-log", status_code=status.HTTP_201_CREATED, response_model=RecordGeminiLogResponse)
async def record_gemini_log(log_data: dict[str, Any], current_user: UserProfileDTO = Depends(get_current_user)) -> RecordGeminiLogResponse:
    """Logs an AI interaction. Available to all authenticated users/agents."""
    dto_data = cast(LogDataDTO, log_data)
    result = await log_service.record_interaction(str(current_user.id), dto_data)

    log_entry = LogEntry(**result["log"]) if "log" in result else None
    return RecordGeminiLogResponse(log=log_entry, error=result.get("error"))


@router.get("/alerts")
async def get_system_alerts(current_user: dict = Depends(requires_permission(TASK_READ_TEAM))):
    """Charlie checks for system alerts and operational errors. Requires Manager visibility."""
    return await log_service.get_active_alerts()
