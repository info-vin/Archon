from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth.dependencies import get_current_user
from ..services.health_service import HealthService

router = APIRouter(prefix="/api/system", tags=["System"])

async def require_system_admin(user=Depends(get_current_user)):
    """
    Dependency to ensure the user has SYSTEM_ADMIN role.
    """
    # Use string comparison as EmployeeRole enum is not yet standardized in backend
    role = (user.get("role") or "").lower()
    if role not in ["system_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Requires System Administrator privileges."
        )
    return user

async def require_manager_or_admin(user=Depends(get_current_user)):
    """
    Dependency to ensure the user has at least MANAGER role.
    """
    role = (user.get("role") or "").lower()
    if role not in ["manager", "admin", "system_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Requires Manager or Admin privileges."
        )
    return user

@router.get("/health/rag", dependencies=[Depends(require_system_admin)])
async def get_rag_health_check() -> dict[str, Any]:
    """
    Performs a deep integrity check of the RAG system.
    WARNING: This performs DB writes (seeding) and should not be called frequently.
    """
    service = HealthService()
    return await service.check_rag_integrity()

@router.get("/settings", dependencies=[Depends(require_manager_or_admin)])
async def list_system_settings(category: str | None = None) -> list[dict[str, Any]]:
    """
    Lists system settings from the database.
    """
    from ..utils import get_supabase_client
    supabase = get_supabase_client()
    query = supabase.table("archon_settings").select("*")
    if category:
        query = query.eq("category", category)
    response = query.order("key").execute()
    return response.data or []

@router.patch("/settings/{key}", dependencies=[Depends(require_manager_or_admin)])

async def update_system_setting(

    key: str,

    request: dict[str, Any],

    current_user: dict = Depends(get_current_user)

) -> dict[str, Any]:

    """
    Updates a specific system setting and records the change in the audit trail.
    """
    from ..config.logfire_config import get_logger  # Ensure logger is available
    from ..utils import get_supabase_client

    logger = get_logger(__name__)
    supabase = get_supabase_client()

    new_value = request.get("value")
    description = request.get("description")

    if new_value is None:
        raise HTTPException(status_code=400, detail="Setting value is required")

    role = current_user.get("role", "viewer").lower()

    # 1. Fetch old value and protection status for auditing/RBAC
    old_res = supabase.table("archon_settings").select("value, is_system_protected").eq("key", key).execute()

    if not old_res.data:
        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")

    old_data = old_res.data[0]
    old_value = old_data["value"]
    is_protected = old_data.get("is_system_protected", False)

    # 1.1 Granular RBAC Check (Charlie protection)
    if is_protected and role == "manager":
        logger.warning(f"API: Manager attempted to edit protected setting | key={key} | user={current_user.get('email')}")
        raise HTTPException(status_code=403, detail="System protected settings can only be edited by Admins.")

    # 2. Perform Update

    update_data = {"value": str(new_value), "updated_at": "now()"}

    if description:

        update_data["description"] = description



    response = supabase.table("archon_settings").update(update_data).eq("key", key).execute()



    if not response.data:

        raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")



    # 3. Create Audit Trail Entry (GAP-022)

    try:

        user_name = current_user.get("name", current_user.get("email", "Unknown"))

        audit_payload = {

            "document_id": f"setting:{key}",

            "created_by": user_name,

            "change_type": "UPDATE",

            "field_name": key,

            "old_value": str(old_value),

            "new_value": str(new_value),

            "change_summary": f"System setting '{key}' updated by {user_name}",

            "version_number": 1

        }

        supabase.table("archon_document_versions").insert(audit_payload).execute()

    except Exception as audit_err:

        from ..config.logfire_config import get_logger

        logger = get_logger(__name__)

        logger.warning(f"Audit logging failed for setting {key}: {audit_err}")



    return dict(response.data[0])


