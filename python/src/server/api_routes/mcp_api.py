"""
MCP API Hardened - Connects Agents to external tools and systems.
Standardized alignment with get_mcp_service_client infrastructure.
"""

import os

from fastapi import APIRouter, Depends

from src.server.config.service_discovery import get_api_url
from src.server.models.auth_models import UserProfileDTO
from src.server.services.mcp_service_client import get_mcp_service_client

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import MCP_MANAGE

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


@router.get("/status")
@router.get("/health")
async def get_mcp_status(current_user: UserProfileDTO = Depends(get_current_user)):
    """General connection status. Available to all authenticated users."""
    client = get_mcp_service_client()
    health = await client.health_check()

    return {
        "status": "healthy" if all(health.values()) else "degraded",
        "details": health,
        "service": "mcp",
    }


@router.get("/sessions")
async def list_mcp_sessions(current_user: UserProfileDTO = Depends(get_current_user)):
    """Get active tool sessions. Frontend expectation."""
    # Placeholder: In a real system, this would query the session manager
    return {"sessions": [], "active_count": 0}


@router.get("/config")
async def get_mcp_config(current_user: dict = Depends(requires_permission(MCP_MANAGE))):
    """Deep inspection of tool configurations. Fetches real system values."""
    api_url = get_api_url()
    mcp_port = os.getenv("ARCHON_MCP_PORT", "8051")
    mcp_transport = os.getenv("MCP_TRANSPORT", "http")

    return {
        "status": "ok",
        "mcp_version": "1.0.0",
        "transport": mcp_transport,
        "port": int(mcp_port),
        "api_endpoint": api_url,
        "host": "localhost" if "localhost" in api_url else "archon-server",
    }


@router.get("/clients")
async def list_mcp_clients(current_user: dict = Depends(requires_permission(MCP_MANAGE))):
    """Placeholder for admin client listing."""
    return []
