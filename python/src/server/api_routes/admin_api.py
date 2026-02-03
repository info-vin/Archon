from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.admin_service import AdminService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

class UpdateRoleRequest(BaseModel):
    role: str

@router.get("/users")
async def get_users(
    limit: int = 100,
    role: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all users (Admin only).
    """
    user_role = current_user.get("role", "viewer").lower()
    if user_role not in ["admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    try:
        users = await AdminService.get_all_users(limit=limit, role_filter=role)
        return users
    except Exception as e:
        logger.error(f"Admin API: Failed to fetch users: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.patch("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    request: UpdateRoleRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a user's role (Admin only).
    """
    user_role = current_user.get("role", "viewer").lower()
    # Double check: Only System Admin or Admin can do this?
    # Let's say Admin can do it for now.
    if user_role not in ["admin", "system_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Prevent Admin from demoting themselves if they are the last admin?
    # Omitted for simplicity in Phase 4.6.4, but good to keep in mind.

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
