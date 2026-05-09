from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from ..auth.dependencies import (
    get_current_user,
    verify_admin_role,
    verify_manager_role,
)
from ..config.logfire_config import get_logger
from ..services.admin_service import AdminService
from ..services.agent_service import agent_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/upload")
async def admin_upload_file(
    file: UploadFile = File(...),
    knowledge_type: str = Form("technical"),
    tags: str = Form("[]"),
    current_user: dict = Depends(get_current_user),
):
    """
    Compatibility endpoint for enduser-ui-fe upload feature.
    Delegates to the standard document upload logic.
    """
    from .knowledge.upload import upload_document

    return await upload_document(file=file, knowledge_type=knowledge_type, tags=tags, current_user=current_user)


class UpdateRoleRequest(BaseModel):
    role: str


class DiagnoseRequest(BaseModel):
    file_path: str


@router.post("/diagnose", dependencies=[Depends(verify_admin_role)])
async def diagnose_file(request: DiagnoseRequest, current_user: dict = Depends(get_current_user)):
    """
    Triggers a technical debt diagnostic for a specific file (Admin only).
    """
    return await agent_service.dev_ops.diagnose_file_health(request.file_path)


@router.get("/users")
async def get_users(limit: int = 100, role: str | None = None, current_user: dict = Depends(get_current_user)):
    """
    Get all users (Admin & Manager).
    """
    user_role = str(current_user.get("role", "viewer")).lower()
    if user_role not in ["admin", "system_admin", "manager"]:
        logger.warning(
            f"Admin API: Unauthorized access attempt to /users by {current_user.get('email')} with role {user_role}"
        )
        raise HTTPException(status_code=403, detail="Insufficient permissions to view team members")

    try:
        users = await AdminService.get_all_users(limit=limit, role_filter=role)
        return {"profiles": users}
    except Exception as e:
        logger.error(f"Admin API: Failed to fetch users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error while fetching users: {str(e)}") from e


@router.patch("/users/{user_id}/role", dependencies=[Depends(verify_admin_role)])
async def update_user_role(user_id: str, request: UpdateRoleRequest, current_user: dict = Depends(get_current_user)):
    """
    Update a user's role (Admin only).
    """
    try:
        email = str(current_user.get("email", "unknown"))
        updated_user = await AdminService.update_user_role(
            user_id=user_id, new_role=request.role, current_admin_email=email
        )
        return updated_user
    except Exception as e:
        logger.error(f"Admin API: Failed to update role: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- RBAC MATRIX MANAGEMENT (Phase 5.4 / Phase 4.6.31 Dynamic) ---


class RBACRoleUpdate(BaseModel):
    role: str
    permissions: list[str]
    description: str | None = None


@router.get("/rbac/matrix", dependencies=[Depends(verify_manager_role)])
async def get_rbac_matrix(current_user: dict = Depends(get_current_user)):
    """Fetch the full role-permission matrix (Managers & Admins)."""
    try:
        return await AdminService.get_rbac_matrix()
    except Exception as e:
        logger.error(f"Admin API: Failed to fetch RBAC matrix: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching matrix") from e


@router.post("/rbac/role", dependencies=[Depends(verify_admin_role)])
async def update_rbac_role(request: RBACRoleUpdate, current_user: dict = Depends(get_current_user)):
    """Update permissions for a specific role (Admin only)."""
    try:
        return await AdminService.update_rbac_role(
            role=request.role, permissions=request.permissions, description=request.description
        )
    except Exception as e:
        logger.error(f"Admin API: Failed to update RBAC role: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- CRAWLER TARGET MANAGEMENT (Phase 1.7 / Phase 4.6.24 Hardened) ---


class CrawlerTargetCreate(BaseModel):
    target_url: str
    max_depth: int = 5
    description: str | None = None


@router.get("/crawler-targets", dependencies=[Depends(verify_manager_role)])
async def list_crawler_targets(
    current_user: dict = Depends(get_current_user)
):
    """List specialized crawler targets (Respects Department Isolation)."""
    from ..utils import get_supabase_client
    query = get_supabase_client().table("archon_crawler_targets").select("*")

    # Physical Isolation logic: If not Admin, filter by department
    if current_user.get("role") not in ["admin", "system_admin"]:
        dept = current_user.get("department", "General")
        query = query.eq("department", dept)

    res = query.order("created_at").execute()
    return res.data or []

@router.post("/crawler-targets", dependencies=[Depends(verify_manager_role)])
async def create_crawler_target(
    request: CrawlerTargetCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a new target associated with the manager's department."""
    from ..utils import get_supabase_client
    data = request.model_dump()
    data["department"] = current_user.get("department", "General")

    res = get_supabase_client().table("archon_crawler_targets").insert(data).execute()
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create target")
    return res.data[0]

@router.delete("/crawler-targets/{target_id}", dependencies=[Depends(verify_manager_role)])

async def delete_crawler_target(target_id: str, current_user: dict = Depends(get_current_user)):
    """Remove a target (Protected by DB RLS for Managers)."""
    from ..utils import get_supabase_client

    # Managers can only delete if RLS allows (matching department)
    get_supabase_client().table("archon_crawler_targets").delete().eq("id", target_id).execute()
    return {"success": True}

@router.get("/logs", dependencies=[Depends(verify_manager_role)])
async def get_admin_logs(
    type: str | None = None,
    time_range: str | None = "7d",
    current_user: dict = Depends(get_current_user)
):
    """Fetch system logs (e.g., AI_CORRECTION)."""
    from datetime import datetime, timedelta

    from ..utils import get_supabase_client

    query = get_supabase_client().table("archon_logs").select("*")

    if type:
        query = query.eq("type", type)

    if time_range:
        days = int(time_range.replace("d", "")) if time_range.endswith("d") else 7
        cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
        query = query.gte("created_at", cutoff_time)

    res = query.order("created_at", desc=True).execute()
    return res.data or []
