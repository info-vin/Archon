"""
Settings API Hardened - Secure management of credentials and users.
Standardized alignment with credential_service infrastructure.
Supports legacy /api prefix for frontend compatibility.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from src.server.schemas.settings import (
    CredentialCreate,
    CredentialResponse,
    CredentialStatusRequest,
    UserUpdateRequest,
)
from src.server.services.credential_service import credential_service
from src.server.services.profile_service import ProfileService
from src.server.services.settings_service import SettingsService

from ..auth.dependencies import get_current_user, get_current_user_optional, requires_permission
from ..auth.permissions import USER_MANAGE

# Use no prefix here, managed by main.py
router = APIRouter(tags=["settings"])

# Define optional settings with their default values (from legacy architecture)
OPTIONAL_SETTINGS_WITH_DEFAULTS = {
    "DISCONNECT_SCREEN_ENABLED": "true",
    "PROJECTS_ENABLED": "true",
    "LOGFIRE_ENABLED": "false",
    "STYLE_GUIDE_ENABLED": "false",
    "MODEL_CHOICE": "gemini-1.5-flash",
}

def get_credential_service():
    """Export for test compatibility."""
    return credential_service

@router.get("/database/metrics")
async def database_metrics(current_user: dict = Depends(get_current_user)):
    """Get database metrics and statistics. Frontend expectation."""
    try:
        settings_service = SettingsService()
        success, tables_info = settings_service.get_database_statistics()
        if not success:
            raise HTTPException(status_code=500, detail={"error": tables_info})

        return {
            "status": "healthy",
            "database": "supabase",
            "tables": tables_info,
            "total_records": sum(tables_info.values()) if isinstance(tables_info, dict) else 0,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e

@router.post("/credentials/status-check")
async def check_credentials_status(
    req: CredentialStatusRequest | None = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Checks if configured AI keys or specific requested keys exist.
    """
    if req and req.keys:
        return await credential_service.check_credentials_exist(req.keys)

    # Default behavior for general status check
    target_keys = ["GOOGLE_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
    return await credential_service.check_credentials_exist(target_keys)

@router.get("/credentials")
async def list_credentials(
    category: str | None = None,
    current_user: dict = Depends(get_current_user)
):
    """Lists all credentials or filters by category. Restricted to Admin."""
    all_creds = await credential_service.list_all_credentials()
    if category:
        return [c for c in all_creds if getattr(c, 'category', '') == category]
    return all_creds

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    current_user: dict = Depends(requires_permission(USER_MANAGE))
):
    """Reset user password to default (Admin only)."""
    # DX-001 Standard Password
    DEFAULT_PW = "qwer45tyuiop"
    from ..utils import get_supabase_client
    try:
        get_supabase_client().auth.admin.update_user_by_id(user_id, {"password": DEFAULT_PW})
        return {"success": True, "message": "Password reset to default successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.get("/credentials/categories/{category}")
async def get_credentials_by_category(
    category: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all credentials for a specific category.
    Frontend compatibility endpoint.
    """
    credentials = await credential_service.get_credentials_by_category(category)
    return {"credentials": credentials}

@router.get("/credentials/{key}")
async def get_credential(
    key: str,
    current_user: dict | None = Depends(get_current_user_optional)
):
    """
    Fetch a specific credential.
    Public UI settings can be fetched without authentication.
    Other settings require a valid user token.
    """
    if current_user is None and key not in OPTIONAL_SETTINGS_WITH_DEFAULTS:
        # Enforce authentication for all non-public keys
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to fetch this setting"
        )

    val = await credential_service.get_credential(key)
    if val is None:
        if key in OPTIONAL_SETTINGS_WITH_DEFAULTS:
            return {
                "key": key,
                "value": OPTIONAL_SETTINGS_WITH_DEFAULTS[key],
                "is_encrypted": False,
                "category": "features"
            }
        raise HTTPException(status_code=404, detail={"error": "Credential not found"})
    return {"key": key, "value": val}

@router.post("/credentials", response_model=CredentialResponse)
async def create_credential(
    req: CredentialCreate,
    current_user: dict = Depends(requires_permission(USER_MANAGE))
):
    """Creates or updates a credential. Admin only."""
    success = await credential_service.set_credential(
        req.key, req.value, req.is_encrypted, req.category, req.description
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to save credential")

    return {
        "key": req.key,
        "value": req.value if not req.is_encrypted else "[ENCRYPTED]",
        "is_encrypted": req.is_encrypted,
        "category": req.category,
        "description": req.description,
        "updated_at": datetime.now().isoformat()
    }

@router.put("/credentials/{key}")
async def update_credential(
    key: str,
    req: dict[str, Any],
    current_user: dict = Depends(requires_permission(USER_MANAGE))
):
    """Update an existing credential. Frontend compatibility."""
    value = req.get("value", "")
    is_encrypted = req.get("is_encrypted", False)
    category = req.get("category")
    description = req.get("description")

    success = await credential_service.set_credential(
        key, value, is_encrypted, category, description
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update credential")

    return {"success": True, "message": f"Credential {key} updated successfully"}

@router.delete("/credentials/{key}")
async def delete_credential(
    key: str,
    current_user: dict = Depends(requires_permission(USER_MANAGE))
):
    """Deletes a credential. Admin only."""
    success = await credential_service.delete_credential(key)
    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"status": "deleted", "success": True}

@router.get("/users")
async def list_users(current_user: dict = Depends(requires_permission(USER_MANAGE))):
    """Lists all system users. Admin only."""
    ok, users = ProfileService().list_all_users()
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to list users")
    return users

@router.put("/users/me")
async def update_own_profile(
    req: UserUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Users can update their own metadata (avatar, name)."""
    ok, res = ProfileService().update_profile(str(current_user.get("id")), req.model_dump(exclude_unset=True))
    if not ok:
        raise HTTPException(status_code=400, detail=str(res))
    return res

@router.put("/users/{user_id}")
async def update_user_role(
    user_id: str,
    req: UserUpdateRequest,
    current_user: dict = Depends(requires_permission(USER_MANAGE))
):
    """Admins update user roles or departments."""
    ok, res = ProfileService().update_profile(user_id, req.model_dump(exclude_unset=True))
    if not ok:
        raise HTTPException(status_code=400, detail=str(res))
    return res
