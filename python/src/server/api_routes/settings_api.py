"""
Settings API Hardened - Secure management of credentials and users.
Standardized alignment with credential_service infrastructure.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.server.auth.dependencies import get_current_user, requires_permission
from src.server.auth.permissions import USER_MANAGE
from src.server.schemas.settings import (
    CredentialCreate,
    CredentialResponse,
    UserUpdateRequest,
)
from src.server.services.credential_service import credential_service
from src.server.services.profile_service import ProfileService

router = APIRouter(prefix="/api/settings", tags=["settings"])

def get_credential_service():
    """Export for test compatibility."""
    return credential_service

@router.post("/credentials/status-check", response_model=dict[str, dict[str, Any]])
async def check_credentials_status(current_user: dict = Depends(get_current_user)):
    """Checks if key AI credentials exist in the system."""
    target_keys = ["GOOGLE_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    return await credential_service.check_credentials_exist(target_keys)

@router.get("/credentials")
async def list_credentials(current_user: dict = Depends(requires_permission(USER_MANAGE))):
    """Lists all credentials. Restricted to Admin."""
    return await credential_service.list_all_credentials()

@router.get("/credentials/{key}")
async def get_credential(key: str, current_user: dict = Depends(requires_permission(USER_MANAGE))):
    """Fetch a specific credential."""
    val = await credential_service.get_credential(key)
    if val is None:
        raise HTTPException(status_code=404, detail={"error": "Credential not found"})
    return {"key": key, "value": val}

@router.post("/credentials", response_model=CredentialResponse)
async def create_credential(req: CredentialCreate, current_user: dict = Depends(requires_permission(USER_MANAGE))):
    """Creates or updates a credential. Admin only."""
    return await credential_service.set_credential(req.key, req.value, req.is_encrypted, req.category, req.description)

@router.delete("/credentials/{key}")
async def delete_credential(key: str, current_user: dict = Depends(requires_permission(USER_MANAGE))):
    """Deletes a credential. Admin only."""
    success = await credential_service.delete_credential(key)
    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"status": "deleted"}

@router.get("/users")
async def list_users(current_user: dict = Depends(requires_permission(USER_MANAGE))):
    """Lists all system users. Admin only."""
    ok, users = ProfileService().list_all_users()
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to list users")
    return users

@router.put("/users/me")
async def update_own_profile(req: UserUpdateRequest, current_user: dict = Depends(get_current_user)):
    """Users can update their own metadata (avatar, name)."""
    ok, res = ProfileService().update_profile(str(current_user.get("id")), req.model_dump(exclude_unset=True))
    if not ok:
        raise HTTPException(status_code=400, detail=str(res))
    return res

@router.put("/users/{user_id}")
async def update_user_role(user_id: str, req: UserUpdateRequest, current_user: dict = Depends(requires_permission(USER_MANAGE))):
    """Admins update user roles or departments."""
    ok, res = ProfileService().update_profile(user_id, req.model_dump(exclude_unset=True))
    if not ok:
        raise HTTPException(status_code=400, detail=str(res))
    return res
