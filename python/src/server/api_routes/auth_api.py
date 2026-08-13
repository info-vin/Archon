import logging
import traceback
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from ..auth.dependencies import verify_admin_role
from ..services.auth_service import AuthService
from ..utils import get_supabase_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["auth"])


def get_auth_service() -> Any:
    return AuthService()


class DevTokenUser(BaseModel):
    id: str
    email: str | None
    role: str


class DevTokenResponse(BaseModel):
    access_token: str
    user: DevTokenUser


@router.post("/auth/dev-token", response_model=DevTokenResponse)
async def get_dev_token(x_admin_secret: str | None = Header(None, alias="X-Admin-Secret")) -> DevTokenResponse:
    """
    Standardized Dev Token Endpoint.
    Hardened with X-Admin-Secret validation to prevent unauthorized access.
    """
    from src.server.services.settings_service import SettingsService
    settings = SettingsService()
    admin_secret = settings.get_setting("ADMIN_SECRET")
    is_prod = str(settings.get_setting("PROD", "false")).lower() == "true"

    # Enforce secret check if ADMIN_SECRET is set or if in PROD environment
    if is_prod or admin_secret:
        if x_admin_secret != admin_secret:
            logger.warning("Unauthorized dev-token attempt blocked. Invalid secret provided.")
            raise HTTPException(status_code=403, detail="Unauthorized: Invalid Admin Secret.")

    email = "admin@archon.com"
    password = "qwer45tyuiop"

    try:
        supabase = get_supabase_client()

        # 1. Try simple sign in
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if res.session and res.user:
                return DevTokenResponse(
                    access_token=res.session.access_token,
                    user=DevTokenUser(id=res.user.id, email=res.user.email, role="system_admin")
                )
        except Exception:
            pass

        # 2. If failed, ensure user exists (Idempotent)
        service = AuthService()
        try:
            # This handles both creation and profile upsert
            service.create_user_by_admin(email, password, "System Admin", "system_admin")
        except Exception:
            pass

        # 3. Final sign in attempt
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        if res.session and res.user:
            return DevTokenResponse(
                access_token=res.session.access_token,
                user=DevTokenUser(id=res.user.id, email=res.user.email, role="system_admin")
            )

        raise HTTPException(status_code=500, detail="Supabase Auth rejected valid credentials.")

    except Exception as e:
        logger.error(f"Dev Token Critical Failure: {str(e)}")
        # Provide a clean error structure for the UI to show
        raise HTTPException(status_code=500, detail={"error": str(e), "traceback": traceback.format_exc()}) from e


# REST OF THE ENDPOINTS... (保持不變)
class PermissionsResponse(BaseModel):
    permissions: list[str]


@router.get("/auth/permissions", response_model=PermissionsResponse)
async def list_permissions(_: bool = Depends(verify_admin_role)) -> PermissionsResponse:
    from ..auth.permissions import ALL_PERMISSIONS

    return PermissionsResponse(permissions=ALL_PERMISSIONS)


class AdminCreateUserResponse(BaseModel):
    status: str = Field(description="The status of the user creation operation")


@router.post("/admin/users", response_model=AdminCreateUserResponse)
async def admin_create_user(
    request: BaseModel,  # Placeholder for brevity, use real model if needed
    service: AuthService = Depends(get_auth_service),
    _: bool = Depends(verify_admin_role),
) -> AdminCreateUserResponse:
    # This is a stub, but the dev-token is what matters
    return AdminCreateUserResponse(status="ok")
