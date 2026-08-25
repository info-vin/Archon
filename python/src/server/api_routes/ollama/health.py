from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from ...config.logfire_config import get_logger
from ...services.llm_provider_service import validate_provider_instance
from ...services.ollama.model_discovery_service import model_discovery_service
from .schemas import (
    InstanceHealthDetail,
    InstanceHealthResponse,
    InstanceHealthSummary,
    InstanceValidationRequest,
    InstanceValidationResponse,
)

logger = get_logger(__name__)
router = APIRouter()


@router.get("/instances/health", response_model=InstanceHealthResponse)
async def health_check_endpoint(
    instance_urls: list[str] = Query(..., description="Ollama instance URLs to check"),
    include_models: bool = Query(False, description="Include model count in response"),
) -> InstanceHealthResponse:
    """Check health status of multiple Ollama instances."""
    try:
        logger.info(f"Checking health for {len(instance_urls)} instances")
        health_results = {}
        for instance_url in instance_urls:
            try:
                url = instance_url.rstrip("/")
                health_status = await model_discovery_service.check_instance_health(url)
                health_results[url] = InstanceHealthDetail(
                    is_healthy=health_status.is_healthy,
                    response_time_ms=health_status.response_time_ms,
                    models_available=health_status.models_available if include_models else None,
                    error_message=health_status.error_message,
                    last_checked=health_status.last_checked,
                )
            except Exception as e:
                logger.warning(f"Health check failed for {instance_url}: {e}")
                health_results[instance_url] = InstanceHealthDetail(
                    is_healthy=False,
                    response_time_ms=None,
                    models_available=None,
                    error_message=str(e),
                    last_checked=None,
                )

        # PERFORMANCE: Replaced sum(1 for ...) and list comprehension with a single pass loop
        healthy_count = 0
        response_times_sum = 0.0
        response_times_count = 0

        for result in health_results.values():
            if result.is_healthy:
                healthy_count += 1

            val = result.response_time_ms
            if val is not None:
                try:
                    response_times_sum += float(str(val))
                    response_times_count += 1
                except (ValueError, TypeError):
                    pass

        avg_response_time = None
        if healthy_count > 0 and response_times_count > 0:
            avg_response_time = response_times_sum / response_times_count

        return InstanceHealthResponse(
            summary=InstanceHealthSummary(
                total_instances=len(instance_urls),
                healthy_instances=healthy_count,
                unhealthy_instances=len(instance_urls) - healthy_count,
                average_response_time_ms=avg_response_time,
            ),
            instance_status=health_results,
            timestamp=datetime.now().isoformat(),
        )
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/validate", response_model=InstanceValidationResponse)
async def validate_instance_endpoint(req: InstanceValidationRequest) -> InstanceValidationResponse:
    """Validate a specific Ollama instance and its capabilities."""
    try:
        url = req.instance_url.rstrip("/")
        logger.info(f"Validating instance: {url}")

        # Fixed: Aligned with actual validate_provider_instance signature
        result = await validate_provider_instance(provider="ollama", instance_url=url)

        health_status = await model_discovery_service.check_instance_health(url)

        return InstanceValidationResponse(
            is_valid=result.get("is_valid", False),
            instance_url=url,
            response_time_ms=result.get("response_time_ms"),
            models_available=health_status.models_available,
            error_message=result.get("error"),
            capabilities=result.get("capabilities", {}),
            health_status={
                "is_healthy": health_status.is_healthy,
                "last_checked": health_status.last_checked,
                "error": health_status.error_message,
            },
        )
    except Exception as e:
        logger.error(f"Error validating instance {req.instance_url}: {e}")
        return InstanceValidationResponse(
            is_valid=False,
            instance_url=req.instance_url,
            response_time_ms=None,
            models_available=0,
            error_message=str(e),
            capabilities={},
            health_status={"is_healthy": False, "error": str(e)},
        )
