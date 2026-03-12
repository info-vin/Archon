from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.dependencies import get_current_user, verify_admin_role
from ..config.logfire_config import get_logger
from ..services.admin_service import AdminService
from ..services.agent_service import agent_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

class UpdateRoleRequest(BaseModel):
    role: str

class DiagnoseRequest(BaseModel):
    file_path: str

@router.post("/diagnose", dependencies=[Depends(verify_admin_role)])
async def diagnose_file(
    request: DiagnoseRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Triggers a technical debt diagnostic for a specific file (Admin only).
    """
    return await agent_service.diagnose_file_health(request.file_path)

@router.get("/users")
async def get_users(
    limit: int = 100,
    role: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all users (Admin & Manager).
    """
    user_role = str(current_user.get("role", "viewer")).lower()
    if user_role not in ["admin", "system_admin", "manager"]:
        logger.warning(f"Admin API: Unauthorized access attempt to /users by {current_user.get('email')} with role {user_role}")
        raise HTTPException(status_code=403, detail="Insufficient permissions to view team members")

    try:
        users = await AdminService.get_all_users(limit=limit, role_filter=role)
        return {"profiles": users}
    except Exception as e:
        logger.error(f"Admin API: Failed to fetch users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error while fetching users: {str(e)}") from e

@router.patch("/users/{user_id}/role", dependencies=[Depends(verify_admin_role)])
async def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a user's role (Admin only).
    """
    try:
        email = str(current_user.get("email", "unknown"))
        updated_user = await AdminService.update_user_role(
            user_id=user_id,
            new_role=request.role,
            current_admin_email=email
        )
        return updated_user
    except Exception as e:
        logger.error(f"Admin API: Failed to update role: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

# --- CRAWLER TARGET MANAGEMENT (Phase 1.7 / BUG-048) ---

class CrawlerTargetCreate(BaseModel):
    target_url: str
    max_depth: int = 5
    description: str | None = None

@router.get("/crawler-targets", dependencies=[Depends(verify_admin_role)])
async def list_crawler_targets(
    current_user: dict = Depends(get_current_user)
):
    """List all specialized crawler targets (Admin only)."""
    from ..utils import get_supabase_client
    res = get_supabase_client().table("archon_crawler_targets").select("*").order("created_at").execute()
    return res.data or []

@router.post("/crawler-targets", dependencies=[Depends(verify_admin_role)])
async def create_crawler_target(
    request: CrawlerTargetCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a new target to the isolated crawler registry (Admin only)."""
    from ..utils import get_supabase_client
    res = get_supabase_client().table("archon_crawler_targets").insert(request.model_dump()).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create target")
    return res.data[0]

@router.delete("/crawler-targets/{target_id}", dependencies=[Depends(verify_admin_role)])
async def delete_crawler_target(
    target_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove a target from the registry (Admin only)."""
    from ..utils import get_supabase_client
    get_supabase_client().table("archon_crawler_targets").delete().eq("id", target_id).execute()
    return {"success": True}
