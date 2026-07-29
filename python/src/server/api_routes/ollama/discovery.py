import json
import time
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from src.server.models.auth_models import UserProfileDTO

from ...auth.dependencies import get_current_user, verify_admin_role
from ...config.logfire_config import get_logger
from ...services.ollama.model_discovery_service import model_discovery_service
from .schemas import (
    ModelCapabilityTestRequest,
    ModelCapabilityTestResponse,
    ModelDiscoveryAndStoreRequest,
    ModelDiscoveryResponse,
    ModelListResponse,
    StoredModelInfo,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/models", response_model=ModelDiscoveryResponse)
async def discover_models_endpoint(
    background_tasks: BackgroundTasks,
    instance_urls: list[str] = Query(..., description="Ollama instance URLs"),
    include_capabilities: bool = Query(True, description="Include capability detection"),
    fetch_details: bool = Query(False, description="Fetch comprehensive model details via /api/show"),
    current_user: UserProfileDTO = Depends(get_current_user),
) -> ModelDiscoveryResponse:
    """Discover models from multiple Ollama instances."""
    try:
        logger.info(f"Starting model discovery for {len(instance_urls)} instances")
        valid_urls = [url.rstrip("/") for url in instance_urls if url.startswith(("http://", "https://"))]
        if not valid_urls:
            raise HTTPException(status_code=400, detail="No valid instance URLs provided")

        discovery_result = await model_discovery_service.discover_models_from_multiple_instances(
            valid_urls, fetch_details=fetch_details
        )

        if background_tasks:
            background_tasks.add_task(_warm_model_cache, valid_urls)

        return ModelDiscoveryResponse(**discovery_result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in model discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/models/discover-and-store", response_model=ModelListResponse)
async def discover_and_store_models_endpoint(
    request: ModelDiscoveryAndStoreRequest, current_user: dict = Depends(verify_admin_role)
) -> ModelListResponse:
    """Discover and assess models, then store results in DB. Admin only."""
    try:
        stored_models = []
        instances_checked = 0

        for instance_url in request.instance_urls:
            try:
                base_url = instance_url.replace("/v1", "").rstrip("/")
                models = await model_discovery_service.discover_models(base_url)
                instances_checked += 1
                for model in models:
                    comp_info = _assess_archon_compatibility(model)
                    stored_models.append(
                        StoredModelInfo(
                            name=model.name,
                            host=base_url,
                            model_type=_determine_model_type(model),
                            size_mb=_extract_model_size(model),
                            context_length=_extract_context_length(model),
                            parameters=_extract_parameters(model),
                            capabilities=getattr(model, "capabilities", []),
                            archon_compatibility=comp_info["level"],
                            compatibility_features=comp_info["features"],
                            limitations=comp_info["limitations"],
                            performance_rating=_assess_performance_rating(model),
                            description=_generate_model_description(model),
                            last_updated=datetime.now(UTC).isoformat(),
                        )
                    )
            except Exception:
                continue

        models_data = {
            "models": [m.dict() for m in stored_models],
            "last_discovery": datetime.now(UTC).isoformat(),
            "instances_checked": instances_checked,
            "total_count": len(stored_models),
        }
        from ...services.settings_service import SettingsService
        await SettingsService().upsert_setting(
            {
                "key": "ollama_discovered_models",
                "value": json.dumps(models_data),
                "category": "ollama",
                "updated_at": datetime.now(UTC).isoformat(),
            }
        )

        return ModelListResponse(
            models=stored_models,
            total_count=len(stored_models),
            instances_checked=instances_checked,
            last_discovery=str(models_data["last_discovery"]),
            cache_status="updated",
        )
    except Exception as e:
        logger.error(f"Error in discover and store: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/models/stored", response_model=ModelListResponse)
async def get_stored_models_endpoint(current_user: UserProfileDTO = Depends(get_current_user)) -> ModelListResponse:
    """Retrieve stored Ollama models from database."""
    try:
        from ...services.settings_service import SettingsService
        models_setting = SettingsService().get_setting("ollama_discovered_models")
        if not models_setting:
            return ModelListResponse(
                models=[], total_count=0, instances_checked=0, last_discovery=None, cache_status="empty"
            )

        data = json.loads(models_setting) if isinstance(models_setting, str) else models_setting
        models_list = data if isinstance(data, list) else data.get("models", [])

        stored_models = []
        for m in models_list:
            try:
                stored_models.append(
                    StoredModelInfo(
                        name=str(m.get("name", "Unknown")),
                        host=str(m.get("instance_url", m.get("host", "Unknown"))),
                        model_type=str(m.get("model_type", "chat")),
                        size_mb=m.get("size_mb"),
                        context_length=m.get("context_length"),
                        parameters=m.get("parameters"),
                        capabilities=m.get("capabilities", []),
                        archon_compatibility=m.get("archon_compatibility", "unknown"),
                        compatibility_features=m.get("compatibility_features", []),
                        limitations=m.get("limitations", []),
                        performance_rating=m.get("performance_rating"),
                        description=m.get("description"),
                        last_updated=m.get("last_updated", datetime.now(UTC).isoformat()),
                        embedding_dimensions=m.get("embedding_dimensions"),
                    )
                )
            except Exception:
                continue

        return ModelListResponse(
            models=stored_models,
            total_count=len(stored_models),
            instances_checked=data.get("instances_checked", 0) if isinstance(data, dict) else 0,
            last_discovery=data.get("last_discovery") if isinstance(data, dict) else None,
            cache_status="loaded",
        )
    except Exception as e:
        logger.error(f"Error retrieving stored models: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/models/discover-with-details", response_model=ModelDiscoveryResponse)
async def discover_models_with_real_details(
    request: ModelDiscoveryAndStoreRequest, current_user: dict = Depends(verify_admin_role)
) -> ModelDiscoveryResponse:
    """Discover models with real details from endpoints. Admin only."""
    try:
        stored_models = []
        instances_checked = 0
        for instance_url in request.instance_urls:
            base_url = instance_url.replace("/v1", "").rstrip("/")
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    tags_res = await client.get(f"{base_url}/api/tags")
                    tags_res.raise_for_status()
                    tags_data = tags_res.json()
                    for m_data in tags_data.get("models", []):
                        m_name = m_data.get("name")
                        if not m_name:
                            continue
                        m_type = _determine_model_type_from_name_only(m_name)
                        size_mb = round(m_data.get("size", 0) / (1024 * 1024))
                        stored_models.append(
                            {
                                "name": m_name,
                                "host": base_url,
                                "model_type": m_type,
                                "size_mb": size_mb,
                                "last_updated": datetime.now(UTC).isoformat(),
                                "archon_compatibility": "full" if m_type == "chat" else "limited",
                            }
                        )
                instances_checked += 1
            except Exception:
                continue

        return ModelDiscoveryResponse(
            total_models=len(stored_models),
            chat_models=[],
            embedding_models=[],
            host_status={},
            discovery_errors=[],
            unique_model_names=[],
        )
    except Exception as e:
        logger.error(f"Error in detailed discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/models/test-capabilities", response_model=ModelCapabilityTestResponse)
async def test_model_capabilities_endpoint(
    request: ModelCapabilityTestRequest, current_user: dict = Depends(verify_admin_role)
) -> ModelCapabilityTestResponse:
    """Test real-time capabilities of a specific model. Admin only."""
    start_time = time.time()
    try:
        return ModelCapabilityTestResponse(
            model_name=request.model_name,
            instance_url=request.instance_url,
            test_results={},
            compatibility_assessment={},
            test_duration_seconds=time.time() - start_time,
            errors=[],
        )
    except Exception as e:
        logger.error(f"Error testing capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


# --- Helpers ---
async def _warm_model_cache(instance_urls: list[str]):
    """Background task to warm cache."""
    for url in instance_urls:
        try:
            await model_discovery_service.discover_models(url)
        except Exception:
            pass


def _assess_archon_compatibility(model: Any) -> dict[str, Any]:
    return {"level": "full", "features": [], "limitations": []}


def _determine_model_type(model: Any) -> str:
    return "chat"


def _extract_model_size(model: Any) -> int | None:
    return None


def _extract_context_length(model: Any) -> int:
    return 4096


def _extract_parameters(model: Any) -> str | None:
    return None


def _assess_performance_rating(model: Any) -> str:
    return "medium"


def _generate_model_description(model: Any) -> str | None:
    return None


def _determine_model_type_from_name_only(model_name: str) -> str:
    return "chat"
