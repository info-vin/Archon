from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger, logfire
from ..utils import get_supabase_client

logger = get_logger(__name__)

router = APIRouter(prefix="/api/ethics", tags=["ethics"])

class EthicsEvent(BaseModel):
    id: str
    severity: str
    event_type: str
    description: str | None
    raw_input: str | None
    created_at: datetime

@router.get("/events", response_model=list[EthicsEvent])
async def get_ethics_events(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """
    Get recent ethics violation events.
    Only accessible by Managers and Admins.
    """
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["manager", "system_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    try:
        supabase = get_supabase_client()
        # Order by created_at desc
        res = supabase.table("archon_ethics_events").select("*").order("created_at", desc=True).limit(limit).execute()

        return res.data
    except Exception as e:
        logfire.error(f"API: Failed to fetch ethics events | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
