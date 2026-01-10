"""
Settings API endpoints for Archon

Handles:
- OpenAI API key management
- Other credentials and configuration
- Settings storage and retrieval
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.dependencies import get_current_admin, get_current_user

# Import logging
from ..config.logfire_config import logfire
from ..services.credential_service import CredentialService, credential_service, initialize_credentials
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
# These are user preferences that should return defaults instead of 404
# This prevents console errors in the frontend when settings haven't been explicitly set
# The frontend can check the 'is_default' flag to know if it's a default or user-set value
OPTIONAL_SETTINGS_WITH_DEFAULTS = {
    "DISCONNECT_SCREEN_ENABLED": "true",  # Show disconnect screen when server is unavailable
    "PROJECTS_ENABLED": "false",  # Enable project management features
    "LOGFIRE_ENABLED": "false",  # Enable Pydantic Logfire integration
    "STYLE_GUIDE_ENABLED": "false",  # Enable Style Guide in navigation
}


@router.get("/credentials/{key}")
async def get_credential(
    key: str,
    cred_service: CredentialService = Depends(get_credential_service),
):
    """Get a specific credential by key."""
    try:
        logfire.info(f"Getting credential | key={key}")
        # Never decrypt - always get metadata only for encrypted credentials
        value = await cred_service.get_credential(key, decrypt=False)

        if value is None:
            # Check if this is an optional setting with a default value
            if key in OPTIONAL_SETTINGS_WITH_DEFAULTS:
                logfire.info(f"Returning default value for optional setting | key={key}")
                return {
                    "key": key,
                    "value": OPTIONAL_SETTINGS_WITH_DEFAULTS[key],
                    "is_default": True,
                    "category": "features",
                    "description": f"Default value for {key}",
                }

            logfire.warning(f"Credential not found | key={key}")
            raise HTTPException(status_code=404, detail={"error": f"Credential {key} not found"})

        logfire.info(f"Credential retrieved successfully | key={key}")

        if isinstance(value, dict) and value.get("is_encrypted"):
            return {
                "key": key,
                "value": "[ENCRYPTED]",
                "is_encrypted": True,
                "category": value.get("category"),
                "description": value.get("description"),
                "has_value": bool(value.get("encrypted_value")),
            }

        # For non-encrypted credentials, return the actual value
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

        # Handle both CredentialUpdateRequest and full Credential object formats
        if isinstance(request, dict):
            # If the request contains a 'value' field directly, use it
            value = request.get("value", "")
            is_encrypted = request.get("is_encrypted")
            category = request.get("category")
            description = request.get("description")
        else:
            value = request.value
            is_encrypted = request.is_encrypted
            category = request.category
            description = request.description

        # Get existing credential to preserve metadata if not provided
        existing_creds = await cred_service.list_all_credentials()
        existing = next((c for c in existing_creds if c.key == key), None)

        if existing is None:
            # If credential doesn't exist, create it
            is_encrypted = is_encrypted if is_encrypted is not None else False
            logfire.info(f"Creating new credential via PUT | key={key}")
        else:
            # Preserve existing values if not provided
            if is_encrypted is None:
                is_encrypted = existing.is_encrypted
            if category is None:
                category = existing.category
            if description is None:
                description = existing.description
            logfire.info(f"Updating existing credential | key={key} | category={category}")

        success = await cred_service.set_credential(
            key=key,
            value=value,
            is_encrypted=is_encrypted,
            category=category,
            description=description,
        )

        if success:
            logfire.info(
                f"Credential updated successfully | key={key} | is_encrypted={is_encrypted}"
            )

            return {"success": True, "message": f"Credential {key} updated successfully"}
        else:
            logfire.error(f"Failed to update credential | key={key}")
            raise HTTPException(status_code=500, detail={"error": "Failed to update credential"})

    except Exception as e:
        logfire.error(f"Error updating credential | key={key} | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.delete("/credentials/{key}")
async def delete_credential(
    key: str,
    cred_service: CredentialService = Depends(get_credential_service),
):
    """Delete a credential."""
    try:
        logfire.info(f"Deleting credential | key={key}")
        success = await cred_service.delete_credential(key)

        if success:
            logfire.info(f"Credential deleted successfully | key={key}")

            return {"success": True, "message": f"Credential {key} deleted successfully"}
        else:
            logfire.error(f"Failed to delete credential | key={key}")
            raise HTTPException(status_code=500, detail={"error": "Failed to delete credential"})

    except Exception as e:
        logfire.error(f"Error deleting credential | key={key} | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.post("/credentials/initialize")
async def initialize_credentials_endpoint():
    """Reload credentials from database."""
    try:
        logfire.info("Reloading credentials from database")
        await initialize_credentials()

        logfire.info("Credentials reloaded successfully")

        return {"success": True, "message": "Credentials reloaded from database"}
    except Exception as e:
        logfire.error(f"Error reloading credentials | error={str(e)}")
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

        total_records = sum(tables_info.values())
        logfire.info(
            f"Database metrics retrieved | total_records={total_records} | tables={tables_info}"
        )

        return {
            "status": "healthy",
            "database": "supabase",
            "tables": tables_info,
            "total_records": total_records,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logfire.error(f"Error getting database metrics | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.get("/settings/health")
async def settings_health():
    """Health check for settings API."""
    logfire.info("Settings health check requested")
    result = {"status": "healthy", "service": "settings"}

    return result


# --- USER PROFILE MANAGEMENT ---

class UserProfileUpdate(BaseModel):
    name: str | None = None
    avatar: str | None = None
    department: str | None = None
    position: str | None = None
    status: str | None = None
    role: str | None = None  # Added for Admin updates
    # Email is sensitive and typically handled by specific flows (auth or admin only)

@router.put("/users/me")
async def update_my_profile(
    updates: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update the currently authenticated user's profile.
    Uses secure JWT token verification via get_current_user dependency.
    """
    user_id = current_user.get("id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Unauthorized: Could not determine user identity")

    try:
        logfire.info(f"Updating profile for user: {user_id}")
        profile_service = ProfileService()

        # Filter out None values
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

        if not update_data:
            return {"success": True, "message": "No changes provided"}

        success, result = profile_service.update_profile(user_id, update_data)

        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to update profile: {result}")

        return {"success": True, "profile": result}

    except HTTPException:
        raise
    except Exception as e:
        logfire.error(f"Error updating my profile | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.put("/users/{user_id}")
async def update_user_profile_admin(
    user_id: str,
    updates: UserProfileUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """
    Admin-only endpoint to update any user's profile.
    Secured by get_current_admin dependency.
    """
    admin_role = current_admin.get("role")

    try:
        logfire.info(f"Admin updating profile for user: {user_id} | admin_role={admin_role}")
        profile_service = ProfileService()

        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

        success, result = profile_service.update_profile(user_id, update_data)

        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to update profile: {result}")

        return {"success": True, "profile": result}

    except HTTPException:
        raise
    except Exception as e:
        logfire.error(f"Error updating user profile (Admin) | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e


@router.get("/users")
async def list_users_admin(
    current_admin: dict = Depends(get_current_admin)
):
    """
    Admin-only endpoint to list all users with full profile details.
    Secured by get_current_admin dependency.
    """
    admin_role = current_admin.get("role")

    try:
        logfire.info(f"Admin listing all users | admin_role={admin_role}")
        profile_service = ProfileService()

        success, result = profile_service.list_full_profiles()

        if not success:
            raise HTTPException(status_code=500, detail=f"Failed to list users: {result}")

        return result

    except HTTPException:
        raise
    except Exception as e:
        logfire.error(f"Error listing users (Admin) | error={str(e)}")
        raise HTTPException(status_code=500, detail={"error": str(e)}) from e
