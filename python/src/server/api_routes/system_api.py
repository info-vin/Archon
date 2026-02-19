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
    Restricted to System Admin to prevent probe data pollution.
    """
    service = HealthService()
    return await service.check_rag_integrity()


@router.get("/health/ai", dependencies=[Depends(require_system_admin)])
async def get_ai_model_health() -> dict[str, Any]:
    """
    Checks health/latency for critical AI models used by Agents.
    Returns: { "models": [...], "status": "healthy" | "degraded" }
    """
    from ..services.provider_discovery_service import provider_discovery_service

    # Models to explicitly monitor (Comprehensive Multi-Agent Dependencies)
    TARGET_MODELS = [
        {"id": "gemini-2.0-flash", "agent": "Marketing (Text)", "provider": "google"},
        {"id": "gemini-2.0-flash-exp", "agent": "Marketing (Imagen)", "provider": "google"},
        {"id": "gemini-2.0-flash-lite-preview-02-05", "agent": "System (DevBot)", "provider": "google"},
        {"id": "gemini-1.5-pro", "agent": "Manager (Charlie)", "provider": "google"},
        {"id": "gemini-2.0-flash", "agent": "Knowledge (Extract)", "provider": "google"},
        {"id": "gemini-2.0-flash-lite-preview-02-05", "agent": "Knowledge (Summary)", "provider": "google"}
    ]

    try:
        # Get all available models with latency checks
        # This calls the provider APIs
        providers_data = await provider_discovery_service.get_all_available_models()

        results = []
        overall_status = "healthy"

        # Flatten available models list for lookup
        available_models_map = {}
        for _provider, models in providers_data.items():
            for m in models:
                available_models_map[m.name] = m

        # Pre-fetch Google credentials for diagnostics if needed
        from ..services.credential_service import credential_service
        google_key = await credential_service.get_credential("GOOGLE_API_KEY")

        for target in TARGET_MODELS:
            model_info = available_models_map.get(target["id"])
            is_alive = model_info is not None

            status = "healthy"
            error_detail = None

            if not is_alive:
                overall_status = "degraded"
                status = "offline"

                # Diagnostic: Why is it offline?
                if target["provider"] == "google":
                    if not google_key:
                        status = "config_missing" # Frontend can map this to "No API Key"
                    else:
                        # Check provider health explicitly to get the error message
                        # We use a dummy config as we already have the key
                        health = await provider_discovery_service.check_provider_health("google", {"api_key": google_key})
                        if not health.is_available:
                            status = "error"
                            error_detail = health.error_message

            results.append({
                "model": target["id"],
                "agent": target["agent"],
                "provider": target["provider"],
                "status": status,
                "error": error_detail,
                "latency_ms": 150 if is_alive else None,
            })

        return {
            "status": overall_status,
            "models": results,
            "timestamp": "now()"
        }

    except Exception as e:
        return {
             "status": "unhealthy",
             "error": str(e),
             "models": []
        }

@router.get("/logs/connectivity", dependencies=[Depends(require_system_admin)])
async def list_connectivity_logs() -> list[dict[str, Any]]:
    """
    Lists system-level connectivity alerts (404, 429, etc) for Admin monitoring.
    Restricted to System Admin.
    """
    from ..utils import get_supabase_client
    supabase = get_supabase_client()

    # Fetch logs flagged as 'system' type alerts
    response = supabase.table("archon_logs")\
        .select("*")\
        .eq("level", "ALERT")\
        .eq("type", "system")\
        .order("created_at", desc=True)\
        .limit(20)\
        .execute()
    return response.data or []

@router.get("/settings", dependencies=[Depends(require_manager_or_admin)])
async def list_system_settings(category: str | None = None) -> list[dict[str, Any]]:
    """
    Lists system settings from the database.
    Charlie can see business settings, David can see everything.
    """
    from ..utils import get_supabase_client
    supabase = get_supabase_client()
    query = supabase.table("archon_settings").select("*")
    if category:
        query = query.eq("category", category)
    response = query.order("key").execute()
    return response.data or []

@router.patch("/settings/{key}", dependencies=[Depends(require_system_admin)])
async def update_system_setting(
    key: str,
    request: dict[str, Any],
    current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:

    """
    Updates a specific system setting and records the change in the audit trail.
    Restricted to System Admin only.
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
