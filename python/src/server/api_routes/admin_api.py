import aiofiles
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from src.server.models.auth_models import UserProfileDTO

from ..auth.dependencies import (
    get_current_user,
    verify_admin_role,
    verify_manager_role,
)
from ..config.logfire_config import get_logger
from ..services.admin_service import admin_service
from ..services.agent_service import agent_service
from ..services.shared_constants import RoleEnum

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])


class UsersListResponse(BaseModel):
    profiles: list[UserProfileDTO] = Field(description="List of user profiles")


@router.post("/scheduler/job/{job_id}/run", dependencies=[Depends(verify_manager_role)])
async def trigger_scheduler_job(job_id: str, background_tasks: BackgroundTasks, current_user: UserProfileDTO = Depends(get_current_user)):
    """
    Phase 5.1.15: Manually trigger a specific Clockwork job from the Admin UI.
    Requires Manager or Admin role.
    """
    from ..services.scheduler_service import scheduler_service

    job_map = {
        "system_probe": scheduler_service._run_system_probe,
        "log_patrol": scheduler_service._run_log_patrol,
        "task_dispatcher": scheduler_service._run_task_dispatcher,
        "model_verification": scheduler_service._run_model_verification,
        "system_probe_cleanup": scheduler_service._cleanup_system_probes,
        "alice_auto_fetch": scheduler_service._run_auto_fetch_leads,
        "bob_market_report": scheduler_service._run_daily_market_report,
        "prune_stale_leads": scheduler_service._run_prune_stale_leads,
        "token_analysis": scheduler_service._analyze_token_usage,
        "business_sentinel": scheduler_service._run_business_sentinel,
        "daily_executive_summary": scheduler_service._run_daily_executive_summary,
        "tech_debt_audit": scheduler_service._run_tech_debt_audit,
        "api_deprecation_scan": scheduler_service._run_api_deprecation_scan,
    }

    if job_id not in job_map:
        raise HTTPException(status_code=400, detail=f"Unknown job_id: {job_id}")

    background_tasks.add_task(job_map[job_id])
    logger.info(f"Admin {current_user.email} manually triggered Clockwork job: {job_id}")
    return {"status": "triggered", "job_id": job_id}


@router.post("/upload")
async def admin_upload_file(
    file: UploadFile = File(...),
    knowledge_type: str = Form("technical"),
    tags: str = Form("[]"),
    current_user: UserProfileDTO = Depends(get_current_user),
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
async def diagnose_file(request: DiagnoseRequest, current_user: UserProfileDTO = Depends(get_current_user)):
    """
    Triggers a technical debt diagnostic for a specific file (Admin only).
    """
    return await agent_service.dev_ops.diagnose_file_health(request.file_path)


@router.get("/david/read", dependencies=[Depends(verify_admin_role)])
async def david_read_file(path: str, current_user: UserProfileDTO = Depends(get_current_user)):
    """
    Allows David Agent to read codebase files for self-evolution (Admin only).
    """
    # Basic security check: ensure the path is within the app directory
    # (The container itself is already limited by Docker mounts)
    if ".." in path or path.startswith("/"):
        raise HTTPException(status_code=400, detail="Invalid path or traversal attempt")

    try:
        async with aiofiles.open(path, encoding="utf-8") as f:
            return await f.read()
    except Exception as e:
        logger.error(f"David Read: Failed to read {path}: {e}")
        raise HTTPException(status_code=404, detail=f"File not found or unreadable: {str(e)}") from e


@router.get("/document-versions")
async def get_document_versions(limit: int = 100, current_user: dict = Depends(verify_admin_role)):
    """
    Get document versions for the Admin audit trail.
    """
    try:
        versions = await admin_service.get_document_versions(limit=limit)
        return {"versions": versions}
    except Exception as e:
        logger.error(f"Admin API: Failed to fetch document versions: {e}")
        return {"versions": []}


@router.get("/users", response_model=UsersListResponse)
async def get_users(limit: int = 100, role: str | None = None, current_user: UserProfileDTO = Depends(get_current_user)) -> UsersListResponse:
    """
    Get all users (Admin & Manager).
    """
    user_role = str(current_user.role).lower()
    if user_role not in [RoleEnum.ADMIN, RoleEnum.SYSTEM_ADMIN, RoleEnum.MANAGER]:
        logger.warning(
            f"Admin API: Unauthorized access attempt to /users by {current_user.email} with role {user_role}"
        )
        raise HTTPException(status_code=403, detail="Insufficient permissions to view team members")

    try:
        from typing import cast
        users = await admin_service.get_all_users(limit=limit, role_filter=role)
        return UsersListResponse(profiles=cast(list[UserProfileDTO], users))
    except Exception as e:
        logger.error(f"Admin API: Failed to fetch users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Database error while fetching users: {str(e)}") from e


@router.patch("/users/{user_id}/role", dependencies=[Depends(verify_admin_role)], response_model=UserProfileDTO)
async def update_user_role(user_id: str, request: UpdateRoleRequest, current_user: UserProfileDTO = Depends(get_current_user)) -> UserProfileDTO:
    """
    Update a user's role (Admin only).
    """
    try:
        email = str(current_user.email)
        updated_user = await admin_service.update_user_role(
            user_id=user_id, new_role=request.role, current_admin_email=email
        )
        return UserProfileDTO.model_validate(updated_user)
    except Exception as e:
        logger.error(f"Admin API: Failed to update role: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- RBAC MATRIX MANAGEMENT (Phase 5.4 / Phase 4.6.31 Dynamic) ---


class RBACRoleUpdate(BaseModel):
    role: str
    permissions: list[str]
    description: str | None = None


class RBACRoleResponse(BaseModel):
    role: str = Field(..., description="The role name")
    permissions: list[str] = Field(..., description="List of permissions assigned to this role")
    description: str | None = Field(None, description="Optional description of the role")


@router.get("/rbac/matrix", dependencies=[Depends(verify_manager_role)], response_model=list[RBACRoleResponse])
async def get_rbac_matrix(current_user: UserProfileDTO = Depends(get_current_user)) -> list[RBACRoleResponse]:
    """Fetch the full role-permission matrix (Managers & Admins)."""
    try:
        data = await admin_service.get_rbac_matrix()
        return [RBACRoleResponse(**role) for role in data]
    except Exception as e:
        logger.error(f"Admin API: Failed to fetch RBAC matrix: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching matrix") from e


@router.post("/rbac/role", dependencies=[Depends(verify_admin_role)], response_model=RBACRoleResponse)
async def update_rbac_role(request: RBACRoleUpdate, current_user: UserProfileDTO = Depends(get_current_user)) -> RBACRoleResponse:
    """Update permissions for a specific role (Admin only)."""
    try:
        data = await admin_service.update_rbac_role(
            role=request.role, permissions=request.permissions, description=request.description
        )
        return RBACRoleResponse(**data)
    except Exception as e:
        logger.error(f"Admin API: Failed to update RBAC role: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- CRAWLER TARGET MANAGEMENT (Phase 1.7 / Phase 4.6.24 Hardened) ---


class CrawlerTargetCreate(BaseModel):
    target_url: str
    max_depth: int = 5
    description: str | None = None


class CrawlerTargetResponse(CrawlerTargetCreate):
    id: str
    department: str | None
    created_at: str


@router.get("/crawler-targets", dependencies=[Depends(verify_manager_role)], response_model=list[CrawlerTargetResponse])
async def list_crawler_targets(current_user: UserProfileDTO = Depends(get_current_user)) -> list[CrawlerTargetResponse]:
    """List specialized crawler targets (Respects Department Isolation)."""
    dept = None
    if current_user.role not in [RoleEnum.ADMIN, RoleEnum.SYSTEM_ADMIN]:
        dept = current_user.department
    from typing import cast
    res = await admin_service.list_crawler_targets(department=dept)
    return cast(list[CrawlerTargetResponse], res)


@router.post("/crawler-targets", dependencies=[Depends(verify_manager_role)], response_model=CrawlerTargetResponse, status_code=201)
async def create_crawler_target(request: CrawlerTargetCreate, current_user: UserProfileDTO = Depends(get_current_user)) -> CrawlerTargetResponse:
    """Add a new target associated with the manager's department."""
    data = request.model_dump()
    data["department"] = current_user.department
    try:
        from typing import cast
        res = await admin_service.create_crawler_target(data)
        return cast(CrawlerTargetResponse, res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/crawler-targets/{target_id}", dependencies=[Depends(verify_manager_role)])
async def delete_crawler_target(target_id: str, current_user: UserProfileDTO = Depends(get_current_user)):
    """Remove a target (Protected by DB RLS for Managers)."""
    await admin_service.delete_crawler_target(target_id)
    return {"success": True}


@router.get("/logs", dependencies=[Depends(verify_manager_role)])
async def get_admin_logs(
    type: str | None = None, time_range: str | None = "7d", current_user: UserProfileDTO = Depends(get_current_user)
):
    """Fetch system logs (e.g., AI_CORRECTION)."""
    return await admin_service.get_admin_logs(type=type, time_range=time_range)
