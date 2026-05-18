"""
Core Infrastructure for Archon MCP Server.
Handles lifecycle, context, and shared state.
"""

import logging
import os
import threading
import time
import traceback
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

from mcp.server.fastmcp import FastMCP

# Global initialization lock and flag
_initialization_lock = threading.Lock()
_initialization_complete = False
_shared_context = None

# GLOBAL REGISTRY FOR AGENTS (Phase 4.6.19)
# This lives in the Worker Process memory
GLOBAL_TOOL_REGISTRY = []

logger = logging.getLogger(__name__)


@dataclass
class ArchonContext:
    """
    Context for MCP server.
    No heavy dependencies - just service client for HTTP calls.
    """

    service_client: Any
    health_status: dict | None = None
    startup_time: float | None = None

    def __post_init__(self):
        if self.health_status is None:
            self.health_status = {
                "status": "healthy",
                "api_service": False,
                "agents_service": False,
                "last_health_check": None,
            }
        if self.startup_time is None:
            self.startup_time = time.time()


def get_tool_schema(tool: Any) -> dict:
    """Safely extract tool schema regardless of FastMCP version."""
    if hasattr(tool, "inputSchema"):
        return cast(dict, tool.inputSchema)
    if hasattr(tool, "parameters"):
        return cast(dict, tool.parameters)
    if hasattr(tool, "model_dump"):
        return cast(dict, tool.model_dump().get("inputSchema", {}))
    return {}


async def perform_health_checks(context: ArchonContext):
    """Perform health checks on dependent services via HTTP."""
    try:
        # Check dependent services
        service_health = await context.service_client.health_check()

        if context.health_status is not None:
            context.health_status["api_service"] = service_health.get("api_service", False)
            context.health_status["agents_service"] = service_health.get("agents_service", False)

            # Overall status
            all_critical_ready = context.health_status["api_service"]

            context.health_status["status"] = "healthy" if all_critical_ready else "degraded"
            context.health_status["last_health_check"] = datetime.now().isoformat()

            if not all_critical_ready:
                logger.warning(f"Health check failed: {context.health_status}")
            else:
                logger.info("Health check passed - dependent services healthy")

    except Exception as e:
        logger.error(f"Health check error: {e}")
        if context.health_status is not None:
            context.health_status["status"] = "unhealthy"
            context.health_status["last_health_check"] = datetime.now().isoformat()


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[ArchonContext]:
    """
    Lifecycle manager - ensures tools are registered in the correct process.
    """
    global _initialization_complete, _shared_context, GLOBAL_TOOL_REGISTRY

    # Import dependencies here to avoid circular imports if core is used elsewhere
    from src.server.services.mcp_service_client import get_mcp_service_client
    from src.server.services.mcp_session_manager import get_session_manager

    # Quick check without lock
    if _initialization_complete and _shared_context:
        logger.info(f"♻️ [PID {os.getpid()}] Reusing existing context")
        yield _shared_context
        return

    # Acquire lock for initialization
    with _initialization_lock:
        if _initialization_complete and _shared_context:
            yield _shared_context
            return

        logger.info(f"🚀 [PID {os.getpid()}] Starting MCP server...")

        try:
            get_session_manager()
            service_client = get_mcp_service_client()
            context = ArchonContext(service_client=service_client)
            await perform_health_checks(context)

            # --- PHYSICAL REGISTRY POPULATION (Phase 4.6.19) ---
            # Access the server's tool manager
            raw_tools = server._tool_manager.list_tools()
            GLOBAL_TOOL_REGISTRY = [
                {
                    "type": "function",
                    "function": {"name": t.name, "description": t.description or "", "parameters": get_tool_schema(t)},
                }
                for t in raw_tools
            ]
            logger.info(f"✅ [PID {os.getpid()}] PHYSICAL REGISTRY FINALIZED: {len(GLOBAL_TOOL_REGISTRY)} tools")

            _shared_context = context
            _initialization_complete = True
            yield context

        except Exception as e:
            logger.error(f"💥 Critical error in lifespan setup: {e}")
            logger.error(traceback.format_exc())
            raise
        finally:
            logger.info("🧹 Cleaning up MCP server...")
