# python/src/server/auth/dependencies.py

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..services.profile_service import ProfileService
from .permissions import get_role_permissions
from .utils import get_user_from_token

# Security scheme for OpenAPI docs
security = HTTPBearer()

async def get_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> str:
    """Extracts the Bearer token from the Authorization header."""
    return credentials.credentials

async def get_current_user(
    token: Annotated[str, Depends(get_token)]
) -> dict:
    """
    Validates the token and retrieves the full user profile (including Role) from the database.
    This is the SSOT for "Who is this user?".
    """
    # 1. Verify Identity (Authentication)
    auth_user = await get_user_from_token(token)
    if not auth_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = auth_user.id

    # 2. Retrieve Context (Authorization)
    # We need the Role from the 'profiles' table, not just the Auth user
    profile_service = ProfileService()
    success, profile = profile_service.get_profile(user_id)

    if not success or not profile:
        # Fallback: If profile doesn't exist yet (rare race condition),
        # return basic auth info with default role
        return {
            "id": user_id,
            "email": auth_user.email,
            "role": "employee" # Default safe role
        }

    return profile # Should contain 'role' field

async def get_current_admin(
    current_user: Annotated[dict, Depends(get_current_user)]
) -> dict:
    """Dependency that enforces Admin role."""
    role = current_user.get("role", "").lower()
    if role not in ["admin", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

def requires_permission(permission: str):
    """
    Factory for creating a dependency that checks if the user has a specific permission.
    Usage: @router.get("/", dependencies=[Depends(requires_permission(TASK_CREATE))])
    """
    async def permission_checker(current_user: Annotated[dict, Depends(get_current_user)]):
        role = current_user.get("role", "").lower()
        user_permissions = get_role_permissions(role)

        if permission not in user_permissions:
             raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: User with role '{role}' lacks '{permission}'"
            )
        return current_user

    return permission_checker
