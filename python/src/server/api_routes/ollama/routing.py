from typing import Any, cast

from fastapi import APIRouter, HTTPException, Query

from ...config.logfire_config import get_logger
from ...services.ollama.embedding_router import embedding_router
from ...services.ollama.model_discovery_service import model_discovery_service
from .schemas import EmbeddingRouteRequest, EmbeddingRouteResponse

logger = get_logger(__name__)
router = APIRouter()


@router.post("/embedding/route", response_model=EmbeddingRouteResponse)
async def analyze_embedding_route_endpoint(request: EmbeddingRouteRequest) -> EmbeddingRouteResponse:
    """Analyze optimal routing for embedding operations."""
    try:
        logger.info(f"Analyzing embedding route for {request.model_name} on {request.instance_url}")
        routing_decision = await embedding_router.route_embedding(
            model_name=request.model_name, instance_url=request.instance_url, text_content=request.text_sample
        )
        performance_score = embedding_router._calculate_performance_score(routing_decision.dimensions)
        return EmbeddingRouteResponse(
            target_column=routing_decision.target_column,
            model_name=routing_decision.model_name,
            instance_url=routing_decision.instance_url,
            dimensions=routing_decision.dimensions,
            confidence=routing_decision.confidence,
            fallback_applied=routing_decision.fallback_applied,
            routing_strategy=routing_decision.routing_strategy,
            performance_score=performance_score,
        )
    except Exception as e:
        logger.error(f"Error analyzing embedding route: {e}")
        raise HTTPException(status_code=500, detail=f"Embedding route analysis failed: {str(e)}") from e


@router.get("/embedding/routes")
async def get_available_embedding_routes_endpoint(
    instance_urls: list[str] = Query(..., description="Ollama instance URLs"),
    sort_by_performance: bool = Query(True, description="Sort by performance score"),
) -> dict[str, Any]:
    """Get all available embedding routes across multiple instances."""
    try:
        logger.info(f"Getting embedding routes for {len(instance_urls)} instances")
        routes = await embedding_router.get_available_embedding_routes(instance_urls)
        route_data = []
        for route in routes:
            route_data.append(
                {
                    "model_name": route.model_name,
                    "instance_url": route.instance_url,
                    "dimensions": route.dimensions,
                    "column_name": route.column_name,
                    "performance_score": route.performance_score,
                    "index_type": embedding_router.get_optimal_index_type(route.dimensions),
                }
            )

        dimension_stats: dict[int, dict[str, Any]] = {}
        for route in routes:
            dim = route.dimensions
            if dim not in dimension_stats:
                dimension_stats[dim] = {"count": 0, "models": [], "avg_performance": 0.0}
            stats_entry = dimension_stats[dim]
            stats_entry["count"] += 1
            cast(list[str], stats_entry["models"]).append(route.model_name)
            stats_entry["avg_performance"] += float(route.performance_score)

        for dim_data in dimension_stats.values():
            if dim_data["count"] > 0:
                dim_data["avg_performance"] /= dim_data["count"]

        return {
            "total_routes": len(routes),
            "routes": route_data,
            "dimension_analysis": dimension_stats,
            "routing_statistics": embedding_router.get_routing_statistics(),
        }
    except Exception as e:
        logger.error(f"Error getting embedding routes: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get embedding routes: {str(e)}") from e


@router.delete("/cache")
async def clear_ollama_cache_endpoint() -> dict[str, str]:
    """Clear all Ollama-related caches."""
    try:
        logger.info("Clearing Ollama caches")
        model_discovery_service.model_cache.clear()
        model_discovery_service.capability_cache.clear()
        model_discovery_service.health_cache.clear()
        embedding_router.clear_routing_cache()
        return {"message": "All Ollama caches cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing caches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear caches: {str(e)}") from e
