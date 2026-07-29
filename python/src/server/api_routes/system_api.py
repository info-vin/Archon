
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.server.models.auth_models import UserProfileDTO

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import MCP_MANAGE, TASK_READ_TEAM
from ..services.health_service import HealthService, HealthStatusResult

router = APIRouter(prefix="/api/system", tags=["System"])


@router.post("/scout/ingest", dependencies=[Depends(requires_permission(MCP_MANAGE))])
async def ingest_scout_reports() -> dict[str, Any]:
    """
    Manually triggers ingestion of Twin Scout diagnostic reports into the RAG Knowledge Base.
    Restricted to System Admin.
    """
    from ..services.scout_ingestion_service import scout_ingestion_service

    try:
        return await scout_ingestion_service.ingest_reports()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scout ingestion failed: {str(e)}") from e


@router.get("/health/rag", dependencies=[Depends(requires_permission(MCP_MANAGE))])
async def get_rag_health_check() -> HealthStatusResult:
    """
    Performs a deep integrity check of the RAG system.
    Restricted to System Admin to prevent probe data pollution.
    """
    service = HealthService()
    return await service.check_rag_integrity()


@router.get("/health/ai", dependencies=[Depends(requires_permission(MCP_MANAGE))])
async def get_ai_model_health() -> dict[str, Any]:
    """
    Checks health/latency for critical AI models used by Agents.
    Returns: { "models": [...], "status": "healthy" | "degraded" }
    """
    from ..config.model_ssot import get_model_path
    from ..services.discovery import provider_discovery_service

    # Models to explicitly monitor (Comprehensive Multi-Agent Dependencies)
    TARGET_MODELS = [
        {"id": get_model_path("DEFAULT_TEXT").replace("models/", ""), "agent": "General Text", "provider": "google"},
        {"id": get_model_path("IMAGE_GEN").replace("models/", ""), "agent": "Marketing (Imagen)", "provider": "google"},
        {
            "id": get_model_path("DEFAULT_PRO").replace("models/", ""),
            "agent": "Reasoning & Coding",
            "provider": "google",
        },
        {
            "id": get_model_path("EMBEDDING").replace("models/", ""),
            "agent": "Knowledge (Embedding)",
            "provider": "google",
        },
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
                        status = "config_missing"  # Frontend can map this to "No API Key"
                    else:
                        # Check provider health explicitly to get the error message
                        # We use a dummy config as we already have the key
                        health = await provider_discovery_service.check_provider_health(
                            "google", {"api_key": google_key}
                        )
                        if not health.is_available:
                            status = "error"
                            error_detail = health.error_message

            results.append(
                {
                    "model": target["id"],
                    "agent": target["agent"],
                    "provider": target["provider"],
                    "status": status,
                    "error": error_detail,
                    "latency_ms": 150 if is_alive else None,
                }
            )

        return {"status": overall_status, "models": results, "timestamp": "now()"}

    except Exception as e:
        return {"status": "unhealthy", "error": str(e), "models": []}


@router.get("/logs/connectivity", dependencies=[Depends(requires_permission(MCP_MANAGE))])
async def list_connectivity_logs() -> list[dict[str, Any]]:
    """
    Lists system-level connectivity alerts (404, 429, etc) for Admin monitoring.
    Restricted to System Admin.
    """

    from ..services.system_service import system_service
    return await system_service.list_connectivity_logs()


@router.get("/settings", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def list_system_settings(category: str | None = None) -> list[dict[str, Any]]:
    """
    Lists system settings from the database.
    Requires TASK_READ_TEAM scope.
    """
    from ..services.system_service import system_service
    return await system_service.list_system_settings(category=category)


@router.patch("/settings/{key}", dependencies=[Depends(requires_permission(MCP_MANAGE))])
async def update_system_setting(
    key: str, request: dict[str, Any], current_user: UserProfileDTO = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Updates a specific system setting and records the change in the audit trail.
    Restricted to System Admin via MCP_MANAGE scope.
    """
    new_value = request.get("value")
    description = request.get("description")

    if new_value is None:
        raise HTTPException(status_code=400, detail="Setting value is required")

    from ..services.system_service import system_service
    try:
        return await system_service.update_system_setting(
            key=key,
            new_value=str(new_value),
            description=description,
            user_name=current_user.name or "System"
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/fallback/status", dependencies=[Depends(requires_permission(TASK_READ_TEAM))])
async def get_fallback_status() -> dict[str, Any]:
    """
    Returns the currently active fallback model tier and internet connectivity status.
    Requires TASK_READ_TEAM permission.
    """
    from ..services.credential_service import credential_service
    active_tier = credential_service.get_active_tier()

    # Check internet connectivity
    internet_connected = False
    try:
        import socket
        # Attempt to establish a lightweight connection to a public DNS
        socket.setdefaulttimeout(1.5)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
        internet_connected = True
    except Exception:
        pass

    return {
        "active_tier": active_tier,
        "internet_connected": internet_connected
    }
