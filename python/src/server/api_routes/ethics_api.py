from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import requires_permission
from ..auth.permissions import TASK_READ_TEAM
from ..config.logfire_config import get_logger
from ..utils import get_supabase_client
from .models_ethics import EthicsEvent

logger = get_logger(__name__)

router = APIRouter(prefix="/api/ethics", tags=["ethics"])


@router.get("/events", response_model=list[EthicsEvent])
async def get_ethics_events(limit: int = 20, current_user: dict = Depends(requires_permission(TASK_READ_TEAM))):
    """
    Get recent ethics violation events.
    Accessible by roles with TASK_READ_TEAM scope (Managers/Admins).
    """
    try:
        supabase = get_supabase_client()
        # Order by created_at desc
        res = supabase.table("archon_ethics_events").select("*").order("created_at", desc=True).limit(limit).execute()

        return res.data
    except Exception as e:
        logger.error(f"API: Failed to fetch ethics events | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
