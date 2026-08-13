"""
MCP API Hardened - Connects Agents to external tools and systems.
Standardized alignment with get_mcp_service_client infrastructure.
"""

import os
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.server.config.service_discovery import get_api_url
from src.server.models.auth_models import UserProfileDTO
from src.server.services.mcp_service_client import get_mcp_service_client

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import MCP_MANAGE

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class MCPHealthResponse(BaseModel):
    status: str = Field(description="Health status of the MCP service")
    details: dict[str, Any] = Field(description="Detailed health metrics")
    service: str = Field(description="Service identifier")


class MCPSession(BaseModel):
    pass


class MCPSessionsResponse(BaseModel):
    sessions: list[MCPSession] = Field(default_factory=list, description="Active sessions")
    active_count: int = Field(default=0, description="Count of active sessions")


class MCPConfigResponse(BaseModel):
    status: str = Field(description="Configuration status")
    mcp_version: str = Field(description="MCP version")
    transport: str = Field(description="Transport protocol")
    port: int = Field(description="MCP port")
    api_endpoint: str = Field(description="API endpoint URL")
    host: str = Field(description="Host address")


@router.get("/status", response_model=MCPHealthResponse)
@router.get("/health", response_model=MCPHealthResponse)
async def get_mcp_status(current_user: UserProfileDTO = Depends(get_current_user)) -> MCPHealthResponse:
    """General connection status. Available to all authenticated users."""
    client = get_mcp_service_client()
    health = await client.health_check()

    return MCPHealthResponse(
        status="healthy" if all(health.values()) else "degraded",
        details=health,
        service="mcp",
    )


@router.get("/sessions", response_model=MCPSessionsResponse)
async def list_mcp_sessions(current_user: UserProfileDTO = Depends(get_current_user)) -> MCPSessionsResponse:
    """Get active tool sessions. Frontend expectation."""
    # Placeholder: In a real system, this would query the session manager
    return MCPSessionsResponse(sessions=[], active_count=0)


@router.get("/config", response_model=MCPConfigResponse)
async def get_mcp_config(current_user: dict = Depends(requires_permission(MCP_MANAGE))) -> MCPConfigResponse:
    """Deep inspection of tool configurations. Fetches real system values."""
    api_url = get_api_url()
    from src.server.services.settings_service import SettingsService
    settings = SettingsService()
    mcp_port = settings.get_setting("ARCHON_MCP_PORT", "8051")
    mcp_transport = settings.get_setting("MCP_TRANSPORT", "http")

    return MCPConfigResponse(
        status="ok",
        mcp_version="1.0.0",
        transport=mcp_transport,
        port=int(mcp_port),
        api_endpoint=api_url,
        host="localhost" if "localhost" in api_url else "archon-server",
    )


@router.get("/clients", response_model=list[Any])
async def list_mcp_clients(current_user: dict = Depends(requires_permission(MCP_MANAGE))) -> list[Any]:
    """Placeholder for admin client listing."""
    return []
