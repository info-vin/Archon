"""
Infrastructure and Monitoring tools for Archon MCP Server.
"""

import json
import logging
import time
from datetime import datetime

from mcp.server.fastmcp import Context, FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from src.server.services.mcp_session_manager import get_session_manager

from ..core import perform_health_checks

logger = logging.getLogger(__name__)


def register_infra_tools(mcp: FastMCP):
    """Register infrastructure tools with the MCP server."""

    @mcp.custom_route("/sessions", methods=["GET"])
    async def get_sessions(request: Request) -> Response:
        """Get active session count from FastMCP internal state."""
        active_sessions = 0
        try:
            if hasattr(mcp, "session_manager"):
                if hasattr(mcp.session_manager, "_server_instances"):
                    active_sessions = len(mcp.session_manager._server_instances)
        except Exception as e:
            logger.error(f"Failed to get active sessions: {e}")

        return JSONResponse({"active_sessions": active_sessions})

    @mcp.tool()
    async def health_check(ctx: Context) -> str:
        """Check health status of MCP server and dependencies."""
        try:
            context = getattr(ctx.request_context, "lifespan_context", None)
            if context is None:
                return json.dumps(
                    {
                        "success": True,
                        "status": "starting",
                        "message": "MCP server is initializing...",
                        "timestamp": datetime.now().isoformat(),
                    }
                )

            if hasattr(context, "health_status") and context.health_status:
                await perform_health_checks(context)
                return json.dumps(
                    {
                        "success": True,
                        "health": context.health_status,
                        "uptime_seconds": time.time() - context.startup_time,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            else:
                return json.dumps(
                    {
                        "success": True,
                        "status": "ready",
                        "message": "MCP server is running",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return json.dumps({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()})

    @mcp.tool()
    async def session_info(ctx: Context) -> str:
        """Get current and active session information."""
        try:
            session_manager = get_session_manager()
            session_info_data = {
                "active_sessions": session_manager.get_active_session_count(),
                "session_timeout": session_manager.timeout,
            }
            context = getattr(ctx.request_context, "lifespan_context", None)
            if context and hasattr(context, "startup_time"):
                session_info_data["server_uptime_seconds"] = time.time() - context.startup_time

            return json.dumps(
                {"success": True, "session_management": session_info_data, "timestamp": datetime.now().isoformat()}
            )
        except Exception as e:
            logger.error(f"Session info failed: {e}")
            return json.dumps({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()})
