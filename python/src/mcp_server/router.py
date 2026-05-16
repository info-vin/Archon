import json
import logging
import os
from datetime import datetime
from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .core import GLOBAL_TOOL_REGISTRY, get_tool_schema

logger = logging.getLogger(__name__)


def register_custom_routes(mcp: FastMCP) -> None:
    """Register custom HTTP routes and discovery tools on the FastMCP instance."""

    # Discovery endpoint for Agents (Phase 4.6.19)
    @mcp.tool()
    async def list_tools() -> str:
        """Dynamically list all registered MCP tools using official FastMCP API."""
        try:
            tools = await mcp.list_tools()
            formatted_tools = []
            for tool in tools:
                formatted_tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description or "",
                            "parameters": get_tool_schema(tool),
                        },
                    }
                )

            return json.dumps(
                {
                    "success": True,
                    "tools": formatted_tools,
                    "count": len(formatted_tools),
                    "timestamp": datetime.now().isoformat(),
                },
                indent=2,
            )
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return json.dumps({"success": False, "error": str(e)}, indent=2)

    # Direct RPC Bridge for Agents (Phase 4.6.19)
    @mcp.custom_route("/rpc", methods=["POST"])
    async def mcp_rpc_handler(request: Request) -> Response:
        """Handle standard JSON-RPC requests via POST."""
        global GLOBAL_TOOL_REGISTRY
        try:
            body = await request.json()
            method_name = body.get("method")
            params = body.get("params", {})

            # 1. Discovery handling (Fast path using Worker-local Registry)
            if method_name == "list_tools":
                agent_type = request.headers.get("X-Agent-Type", "anonymous")
                tools_to_return = []

                # FAIL-SAFE A: Try disk cache first
                tools_cache = "/tmp/mcp_tools.json"
                if os.path.exists(tools_cache):
                    try:
                        with open(tools_cache) as f:
                            cached = json.load(f)
                            if cached:
                                tools_to_return = cached
                                logger.info(
                                    f"✅ [PID {os.getpid()}] Discovery: Serving {len(cached)} tools from disk cache for {agent_type}"
                                )
                    except Exception:
                        pass

                # FAIL-SAFE B: If registry is empty, try live fetch
                if not tools_to_return:
                    if not GLOBAL_TOOL_REGISTRY:
                        logger.warning(f"⚠️ [PID {os.getpid()}] Registry empty, triggering fail-safe live fetch")
                        raw_tools = mcp._tool_manager.list_tools()
                        GLOBAL_TOOL_REGISTRY = [
                            {
                                "type": "function",
                                "function": {
                                    "name": t.name,
                                    "description": t.description or "",
                                    "parameters": get_tool_schema(t),
                                },
                            }
                            for t in raw_tools
                        ]
                    tools_to_return = GLOBAL_TOOL_REGISTRY

                # Apply RBAC Filtering (Dynamic Tool Exposing) via RBACService
                from src.server.services.rbac_service import RBACService
                rbac = RBACService()
                restricted_tools = await rbac.get_restricted_mcp_tools(agent_type)

                if restricted_tools:
                    filtered_tools = []
                    for t in tools_to_return:
                        if isinstance(t, dict):
                            func = t.get("function")
                            if isinstance(func, dict) and func.get("name") not in restricted_tools:
                                filtered_tools.append(t)
                    tools_to_return = filtered_tools
                    logger.info(f"🔒 [PID {os.getpid()}] RBAC applied for {agent_type}. Returning {len(tools_to_return)} tools.")

                return JSONResponse({"jsonrpc": "2.0", "result": tools_to_return, "id": body.get("id")})

            # 2. Tool execution via official API
            logger.info(f"RPC Call: [PID {os.getpid()}] Executing tool '{method_name}' via official call_tool API")

            # Apply RBAC Enforcement on Execution via RBACService
            agent_type = request.headers.get("X-Agent-Type", "anonymous")
            from src.server.services.rbac_service import RBACService
            rbac = RBACService()
            restricted_tools = await rbac.get_restricted_mcp_tools(agent_type)

            if method_name in restricted_tools:
                logger.warning(f"🚫 [PID {os.getpid()}] RBAC Violation: {agent_type} attempted to call {method_name}")
                return JSONResponse(
                    {"error": {"code": -32003, "message": f"RBAC Violation: Tool '{method_name}' is restricted for agent '{agent_type}'"}}, status_code=403
                )

            try:
                raw_result = await mcp.call_tool(method_name, params)
            except Exception as tool_err:
                return JSONResponse(
                    {"error": {"code": -32603, "message": f"Tool execution failed: {str(tool_err)}"}}, status_code=500
                )

            # 3. Physical Serialization & Unwrapping
            processed_result: Any = []
            if isinstance(raw_result, list):
                for item in raw_result:
                    if hasattr(item, "model_dump"):
                        dump = item.model_dump()
                        processed_result.append(dump.get("text", "") if dump.get("type") == "text" else dump)
                    else:
                        processed_result.append(str(item))
            else:
                processed_result = str(raw_result)

            return JSONResponse({"jsonrpc": "2.0", "result": processed_result, "id": body.get("id")})
        except Exception as e:
            logger.error(f"RPC Bridge Failed: {e}", exc_info=True)
            return JSONResponse({"error": {"code": -32603, "message": str(e)}}, status_code=500)

    # Custom route for session tracking
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
