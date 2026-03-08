from fastapi import APIRouter

from .discovery import router as discovery_router
from .health import router as health_router
from .routing import router as routing_router

router = APIRouter(prefix="/api/ollama", tags=["ollama"])

# Include sub-routers without prefix to maintain backward compatibility
# The prefix is already handled by the parent router or the original paths
router.include_router(discovery_router)
router.include_router(health_router)
router.include_router(routing_router)
