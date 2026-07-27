# python/src/server/auth/dependencies.py

from typing import Annotated, Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..models.auth_models import UserProfileDTO
from ..services.profile_service import ProfileService
from .utils import get_user_from_token

# Security scheme for OpenAPI docs
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


async def get_token(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> str:
    """Extracts the Bearer token from the Authorization header."""
    return str(credentials.credentials)


async def get_token_optional(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_optional)],
) -> str | None:
    """Extracts the Bearer token if present, otherwise returns None."""
    if not credentials:
        return None
    return str(credentials.credentials)


async def get_current_user(token: Annotated[str, Depends(get_token)]) -> UserProfileDTO:
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
    try:
        success, profile = profile_service.get_profile(user_id)
        if success and profile:
            if isinstance(profile, dict):
                return UserProfileDTO(**profile)
            if isinstance(profile, UserProfileDTO):
                return profile
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning(f"⚠️ Profile fetch failed for {user_id}: {e}. Falling back to metadata.")

    # Fallback: If profile doesn't exist yet (rare race condition or seed mismatch),
    # return basic auth info with default role.
    # Try to get role from user_metadata first.
    fallback_role = "employee"
    if hasattr(auth_user, "user_metadata") and auth_user.user_metadata:
        metadata_role = auth_user.user_metadata.get("role")
        if metadata_role:
            fallback_role = metadata_role

    return UserProfileDTO(id=user_id, email=getattr(auth_user, "email", "system@archon.com") or "system@archon.com", role=fallback_role)


async def get_current_user_optional(token: Annotated[str | None, Depends(get_token_optional)]) -> UserProfileDTO | None:
    """
    Validates the token and retrieves the profile if a token is provided.
    If no token is provided, or the token is invalid, returns None instead of raising 401.
    Useful for endpoints that have public fallback behavior (e.g. public settings).
    """
    if not token:
        return None

    try:
        # We reuse get_current_user logic but catch the 401 to return None
        return await get_current_user(token)
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            return None
        raise e


async def get_current_admin(current_user: Annotated[UserProfileDTO, Depends(get_current_user)]) -> UserProfileDTO:
    """Dependency that enforces Admin role and returns the user object."""
    role = current_user.role.lower()
    if role not in ["admin", "system_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return current_user


async def verify_admin_role(current_user: Annotated[UserProfileDTO, Depends(get_current_user)]) -> bool:
    """Secure boolean-style dependency for Admin enforcement via JWT."""
    role = current_user.role.lower()
    if role not in ["admin", "system_admin"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return True


async def verify_manager_role(current_user: Annotated[UserProfileDTO, Depends(get_current_user)]) -> bool:
    """Secure dependency ensuring the user is at least a Manager or Admin."""
    role = current_user.role.lower()
    if role not in ["admin", "system_admin", "manager"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Manager privileges or higher required")
    return True


async def get_current_user_id(current_user: Annotated[UserProfileDTO, Depends(get_current_user)]) -> str:
    """Extracts the user ID from the current authenticated user."""
    return current_user.id


async def get_propose_change_service() -> Any:
    """Dependency that provides an instance of ProposeChangeService."""
    from ..services.propose_change_service import ProposeChangeService

    return ProposeChangeService()


def requires_permission(permission: str) -> Any:
    """
    Factory for creating a dependency that checks if the user has a specific permission.
    Usage: @router.get("/", dependencies=[Depends(requires_permission(TASK_CREATE))])
    """

    async def permission_checker(current_user: Annotated[UserProfileDTO, Depends(get_current_user)]) -> UserProfileDTO:
        from ..services.rbac_service import RBACService

        role = current_user.role.lower()
        # Phase 4.6.31: Switch to Dynamic RBAC Matrix via RBACService
        user_permissions = await RBACService().get_role_permissions(role)

        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"🛡️ [RBAC Check] User: {current_user.email} | Role: {role} | Checking: {permission}")
        logger.info(f"🔑 [RBAC Matrix] Available for {role}: {user_permissions}")

        if permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: User with role '{role}' lacks '{permission}'",
            )
        return current_user

    return permission_checker
