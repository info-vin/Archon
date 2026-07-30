from fastapi import APIRouter

from ..lifespan import AVAILABLE_AGENTS
from ..models import HealthResponse, RootResponse

router = APIRouter(tags=["health"])

@router.get("/", response_model=RootResponse)
@router.head("/", response_model=RootResponse)
async def root() -> RootResponse:
    """Root endpoint for the agents service"""
    return RootResponse(status="healthy", service="agents")

@router.get("/health", response_model=HealthResponse)
@router.head("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="agents",
        agents_available=list(AVAILABLE_AGENTS.keys()),
        note="This service only hosts PydanticAI agents",
    )
