
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from ..services.auth_service import AuthService
from ..utils import get_supabase_client

router = APIRouter(prefix="/api", tags=["auth"])

class AdminCreateUserRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str
    status: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

class UpdateEmailRequest(BaseModel):
    new_email: str

def get_auth_service():
    return AuthService()

def verify_admin_role(x_user_role: str | None = Header(None, alias="X-User-Role")):
    """
    Simple RBAC check based on trusted header from API Gateway / Client.
    In a real prod env, we would verify the JWT token claims.
    For this migration, we rely on the pattern used in other APIs.
    """
    if x_user_role not in ["system_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return x_user_role

@router.post("/admin/users")
async def admin_create_user(
    request: AdminCreateUserRequest,
    service: AuthService = Depends(get_auth_service),
    _: str = Depends(verify_admin_role)
):
    try:
        profile = service.create_user_by_admin(
            email=request.email,
            password=request.password,
            name=request.name,
            role=request.role,
            status=request.status
        )
        return {"profile": profile}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/auth/register")
async def register_user(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service)
):
    try:
        profile = service.register_user(
            email=request.email,
            password=request.password,
            name=request.name
        )
        return {"profile": profile}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

@router.put("/auth/email")
async def update_email(
    request: UpdateEmailRequest,
    authorization: str | None = Header(None),
    service: AuthService = Depends(get_auth_service)
):
    """
    Update email for the authenticated user.
    Uses the JWT token to identify the user ID.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ")[1]

    try:
        # Get User ID from Supabase using the token
        # We use a non-admin client for this check to verify the token is valid for a user
        # OR we can just decode the JWT if we trust the secret.
        # Safer: Use supabase.auth.get_user(token)
        supabase = get_supabase_client()
        user_response = supabase.auth.get_user(token)

        if not user_response.user:
            raise HTTPException(status_code=401, detail="Invalid token")

        user_id = user_response.user.id

        service.update_user_email(user_id, request.new_email)
        return {"success": True}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/auth/dev-token")
async def get_dev_token():
    """
    Development-only endpoint to auto-login as System Admin.
    Used by Admin UI (archon-ui-main) to maintain seamless DX.
    """
    # TODO: Add strict environment check (e.g. if os.getenv("ENV") != "dev": raise 403)

    try:
        supabase = get_supabase_client()
        email = "admin@archon.ai"
        password = "admin_password_123"

        # 1. Try to sign in
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if auth_response.session:
                return {
                    "access_token": auth_response.session.access_token,
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "role": "system_admin" # Enforced by ProfileService logic later
                    }
                }
        except Exception:
            # Sign in failed (likely user doesn't exist), proceed to create
            pass

        # 2. Create Admin User if not exists
        # Use service_role to create user
        service = AuthService()
        try:
            # Check if user exists but with wrong password?
            # Ideally we'd reset password here but for now just try create
            service.create_user_by_admin(
                email=email,
                password=password,
                name="System Admin",
                role="system_admin",
                status="active"
            )

            # 3. Sign in again
            auth_response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if auth_response.session:
                return {
                    "access_token": auth_response.session.access_token,
                    "user": {
                        "id": auth_response.user.id,
                        "email": auth_response.user.email,
                        "role": "system_admin"
                    }
                }

        except Exception as create_error:
             raise HTTPException(status_code=500, detail=f"Failed to create dev admin: {str(create_error)}") from create_error

        raise HTTPException(status_code=500, detail="Failed to obtain dev token")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
