"""
Settings API endpoints for Archon

Handles:
- OpenAI API key management
- Other credentials and configuration
- Settings storage and retrieval
- User profile management (Admin & Manager)
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.dependencies import get_current_user

# Import logging
from ..config.logfire_config import logfire
from ..services.credential_service import CredentialService, credential_service
from ..services.profile_service import ProfileService
from ..services.settings_service import SettingsService

router = APIRouter(prefix="/api", tags=["settings"])


def get_credential_service() -> CredentialService:
    return credential_service


class CredentialRequest(BaseModel):
    key: str
    value: str
    is_encrypted: bool = False
    category: str | None = None
    description: str | None = None


class CredentialUpdateRequest(BaseModel):
    value: str
    is_encrypted: bool | None = None
    category: str | None = None
    description: str | None = None


class CredentialResponse(BaseModel):
    success: bool
    message: str


class CredentialStatusRequest(BaseModel):
    keys: list[str]


@router.post("/credentials/status-check")
async def check_credential_status(
    request: CredentialStatusRequest,
    cred_service: CredentialService = Depends(get_credential_service),
):
    """Check if a list of credentials have values."""
    try:
        logfire.info(f"Checking status for {len(request.keys)} credentials")
        statuses = await cred_service.check_credentials_exist(request.keys)
        logfire.info(f"Credential status check successful | count={len(statuses)}")
        return statuses
    except Exception as e:
        logfire.error(f"Error checking credential status | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


# Credential Management Endpoints
@router.get("/credentials")
async def list_credentials(
    category: str | None = None,
    cred_service: CredentialService = Depends(get_credential_service),
):
    """List all credentials and their categories."""
    try:
        logfire.info(f"Listing credentials | category={category}")
        credentials = await cred_service.list_all_credentials()

        if category:
            # Filter by category
            credentials = [cred for cred in credentials if cred.category == category]

        result_count = len(credentials)
        logfire.info(
            f"Credentials listed successfully | count={result_count} | category={category}"
        )

        return [
            {
                "key": cred.key,
                "value": cred.value,
                "encrypted_value": cred.encrypted_value,
                "is_encrypted": cred.is_encrypted,
                "category": cred.category,
                "description": cred.description,
            }
            for cred in credentials
        ]
    except Exception as e:
        logfire.error(f"Error listing credentials | category={category} | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.get("/credentials/categories/{category}")
async def get_credentials_by_category(
    category: str,
    cred_service: CredentialService = Depends(get_credential_service),
):
    """Get all credentials for a specific category."""
    try:
        logfire.info(f"Getting credentials by category | category={category}")
        credentials = await cred_service.get_credentials_by_category(category)

        logfire.info(
            f"Credentials retrieved by category | category={category} | count={len(credentials)}"
        )

        return {"credentials": credentials}
    except Exception as e:
        logfire.error(
            f"Error getting credentials by category | category={category} | error={str(e)}"
        )
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/credentials")
async def create_credential(
    request: CredentialRequest,
    cred_service: CredentialService = Depends(get_credential_service),
):
    """Create or update a credential."""
    try:
        logfire.info(
            f"Creating/updating credential | key={request.key} | is_encrypted={request.is_encrypted} | category={request.category}"
        )

        success = await cred_service.set_credential(
            key=request.key,
            value=request.value,
            is_encrypted=request.is_encrypted,
            category=request.category,
            description=request.description,
        )

        if success:
            logfire.info(
                f"Credential saved successfully | key={request.key} | is_encrypted={request.is_encrypted}"
            )

            return {
                "success": True,
                "message": f"Credential {request.key} {'encrypted and ' if request.is_encrypted else ''}saved successfully",
            }
        else:
            logfire.error(f"Failed to save credential | key={request.key}")
            raise HTTPException(status_code=500, detail={"error": "Failed to save credential"})

    except Exception as e:
        logfire.error(f"Error creating credential | key={request.key} | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


# Define optional settings with their default values
OPTIONAL_SETTINGS_WITH_DEFAULTS = {
    "DISCONNECT_SCREEN_ENABLED": "true",
    "PROJECTS_ENABLED": "false",
    "LOGFIRE_ENABLED": "false",
    "STYLE_GUIDE_ENABLED": "false",
}


@router.get("/credentials/{key}")
async def get_credential(
    key: str,
    cred_service: CredentialService = Depends(get_credential_service),
):
    """Get a specific credential by key."""
    try:
        logfire.info(f"Getting credential | key={key}")
        value = await cred_service.get_credential(key, decrypt=False)

        if value is None:
            if key in OPTIONAL_SETTINGS_WITH_DEFAULTS:
                return {
                    "key": key,
                    "value": OPTIONAL_SETTINGS_WITH_DEFAULTS[key],
                    "is_default": True,
                    "category": "features",
                    "description": f"Default value for {key}",
                }
            raise HTTPException(status_code=404, detail={"error": f"Credential {key} not found"})

        if isinstance(value, dict) and value.get("is_encrypted"):
            return {
                "key": key,
                "value": "[ENCRYPTED]",
                "is_encrypted": True,
                "category": value.get("category"),
                "description": value.get("description"),
                "has_value": bool(value.get("encrypted_value")),
            }

        return {"key": key, "value": value, "is_encrypted": False}

    except HTTPException:
        raise
    except Exception as e:
        logfire.error(f"Error getting credential | key={key} | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.put("/credentials/{key}")
async def update_credential(
    key: str,
    request: dict[str, Any],
    cred_service: CredentialService = Depends(get_credential_service),
):
    """Update an existing credential."""
    try:
        logfire.info(f"Updating credential | key={key}")
        value = request.get("value", "")
        is_encrypted = request.get("is_encrypted")
        category = request.get("category")
        description = request.get("description")

        success = await cred_service.set_credential(
            key=key,
            value=value,
            is_encrypted=is_encrypted,
            category=category,
            description=description,
        )

        if success:
            return {"success": True, "message": f"Credential {key} updated successfully"}
        raise HTTPException(status_code=500, detail={"error": "Failed to update credential"})
    except Exception as e:
        logfire.error(f"Error updating credential | key={key} | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.get("/database/metrics")
async def database_metrics():
    """Get database metrics and statistics."""
    try:
        logfire.info("Getting database metrics")
        settings_service = SettingsService()
        success, tables_info = settings_service.get_database_statistics()
        if not success:
            raise HTTPException(status_code=500, detail={"error": tables_info})
        return {
            "status": "healthy",
            "database": "supabase",
            "tables": tables_info,
            "total_records": sum(tables_info.values()),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logfire.error(f"Error getting database metrics | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


# --- USER PROFILE MANAGEMENT ---

class UserProfileUpdate(BaseModel):
    name: str | None = None
    avatar: str | None = None
    department: str | None = None
    position: str | None = None
    status: str | None = None
    role: str | None = None

class ResetPasswordRequest(BaseModel):
    new_password: str

@router.put("/users/me")
async def update_my_profile(
    updates: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update authenticated user's profile."""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        profile_service = ProfileService()
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        success, result = profile_service.update_profile(user_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to update profile: {result}")
        return {"success": True, "profile": result}
    except Exception as e:
        logfire.error(f"Error updating profile | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e

@router.get("/users")
async def list_users_admin(
    current_user: dict = Depends(get_current_user)
):
    """List users (Admins see all, Managers see department)."""
    role = current_user.get("role")
    dept = current_user.get("department")
    if role not in ["admin", "system_admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        profile_service = ProfileService()
        success, all_users = profile_service.list_full_profiles()
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to list users: {all_users}")
        if role in ["admin", "system_admin"]:
            return all_users
        if role == "manager":
            return [u for u in all_users if u.get('department') == dept] if dept else [u for u in all_users if u['id'] == current_user['id']]
        return []
    except Exception as e:
        logfire.error(f"Error listing users | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e

@router.put("/users/{user_id}")
async def update_user_profile_admin(
    user_id: str,
    updates: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update any user profile (Admin/Manager with safety)."""
    role = current_user.get("role")
    dept = current_user.get("department")
    if role not in ["admin", "system_admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        profile_service = ProfileService()
        if role == "manager":
            success, target = profile_service.get_profile(user_id)
            if not success or not target:
                raise HTTPException(status_code=404, detail="User not found")
            if target.get("department") != dept:
                raise HTTPException(status_code=403, detail="Out of department")
            if target.get("role") in ["admin", "system_admin"]:
                raise HTTPException(status_code=403, detail="Cannot modify Admin")
            if updates.department and updates.department != dept:
                raise HTTPException(status_code=403, detail="Cannot transfer department")
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
        success, result = profile_service.update_profile(user_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail=f"Failed: {result}")
        return {"success": True, "profile": result}
    except HTTPException:
        raise
    except Exception as e:
        logfire.error(f"Error updating user profile | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e

@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    request: ResetPasswordRequest,
    current_user: dict = Depends(get_current_user)
):
    """Reset user password (Admin/Manager with safety)."""
    role = current_user.get("role")
    dept = current_user.get("department")
    if role not in ["admin", "system_admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    try:
        profile_service = ProfileService()
        if role == "manager":
            success, target = profile_service.get_profile(user_id)
            if not success or not target:
                raise HTTPException(status_code=404, detail="User not found")
            if target.get("department") != dept:
                raise HTTPException(status_code=403, detail="Out of department")
            if target.get("role") in ["admin", "system_admin"]:
                raise HTTPException(status_code=403, detail="Cannot modify Admin")
        from ..utils import get_supabase_client
        supabase = get_supabase_client()
        supabase.auth.admin.update_user_by_id(user_id, {"password": request.new_password})
        return {"success": True, "message": "Password reset successfully"}
    except Exception as e:
        logfire.error(f"Password reset failed | error={str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) from e
