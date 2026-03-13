"""
MCP API Hardened - Connects Agents to external tools and systems.
Standardized alignment with get_mcp_service_client infrastructure.
"""


from fastapi import APIRouter, Depends

from src.server.auth.dependencies import get_current_user, requires_permission
from src.server.auth.permissions import MCP_MANAGE
from src.server.services.mcp_service_client import get_mcp_service_client

router = APIRouter(prefix="/api/mcp", tags=["mcp"])

@router.get("/status")
async def get_mcp_status(current_user: dict = Depends(get_current_user)):
    """General connection status. Available to all authenticated users."""
    client = get_mcp_service_client()
    return await client.health_check()

@router.get("/config")
async def get_mcp_config(current_user: dict = Depends(requires_permission(MCP_MANAGE))):
    """Deep inspection of tool configurations. Restricted to Admin."""
    # Placeholder for config access if needed
    return {"status": "ok", "mcp_version": "1.0.0"}

@router.get("/clients")
async def list_mcp_clients(current_user: dict = Depends(requires_permission(MCP_MANAGE))):
    """Placeholder for admin client listing."""
    return []
