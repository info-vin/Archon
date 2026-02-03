"""
API endpoint for logging Gemini interactions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.log_service import LogService
from ..utils import get_supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["Logging"])

class GeminiLogRequest(BaseModel):
    user_input: str | None = None
    gemini_response: str
    project_name: str | None = None
    user_name: str | None = None

@router.post("/record-gemini-log", status_code=status.HTTP_201_CREATED)
async def record_gemini_log(request: GeminiLogRequest):
    """
    Receives a log of a Gemini interaction and records it in the database.
    """
    try:
        logger.info(f"Received request to log Gemini interaction for project: {request.project_name}")

        log_service = LogService()
        success, result = log_service.create_log_entry(request.dict())

        if not success:
            logger.error(f"Failed to create log entry: {result.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "An unknown error occurred.")
            )

        logger.info(f"Successfully recorded log entry with ID: {result['log']['id']}")
        return {"message": "Log recorded successfully", "log_id": result['log']['id']}

    except HTTPException:
        # Re-raise HTTPException to prevent it from being caught by the generic Exception handler
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred while recording a Gemini log: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred."
        ) from e

@router.get("/logs/alerts")
async def get_alerts(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Fetch active alerts for the Manager Dashboard.
    Strictly filtered to 'ALERT' level for security.
    """
    try:
        user_role = current_user.get("role", "viewer").lower()
        # Only managers and admins can view alerts
        if user_role not in ["manager", "admin", "system_admin"]:
            logger.warning(f"API: Alert fetch denied | user={current_user.get('email')} | role={user_role}")
            raise HTTPException(status_code=403, detail="Insufficient permissions to view alerts.")

        supabase = get_supabase_client()
        # FB-07: Filter out already dispatched alerts (status='dispatched' in JSONB details)
        # Note: We filter for NULL status or not 'dispatched'
        res = supabase.table("archon_logs")\
            .select("*")\
            .eq("level", "ALERT")\
            .or_("details->>status.is.null,details->>status.neq.dispatched")\
            .order("created_at", desc=True)\
            .limit(limit)\
            .execute()

        logger.info(f"API: Alerts fetched | count={len(res.data) if res.data else 0} | user={current_user.get('email')}")
        return res.data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API: Failed to fetch alerts | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
