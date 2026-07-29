"""
MCP Client for Agents

This lightweight client allows PydanticAI agents to call MCP tools via HTTP.
Agents use this client to access all data operations through the MCP protocol
instead of direct database access or service imports.
"""

import json
import logging
from typing import Any

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MCPToolSchema(BaseModel):
    name: str
    description: str | None = None
    input_schema: dict[str, Any] | None = Field(default_factory=dict, alias="inputSchema")


class MCPClient:
    """Client for calling MCP tools via HTTP."""

    def __init__(self, mcp_url: str | None = None, agent_type: str | None = None):
        """
        Initialize MCP client.

        Args:
            mcp_url: MCP server URL (defaults to service discovery)
            agent_type: Optional string identifier for the calling agent (used for RBAC)
        """
        self.agent_type = agent_type

        if mcp_url:
            self.mcp_url = mcp_url
        else:
            # Use service discovery to find MCP server
            try:
                from ..server.config.service_discovery import get_mcp_url

                self.mcp_url = get_mcp_url()
            except ImportError:
                # Fallback for when running in agents container
                import os
                from pathlib import Path

                mcp_port = os.getenv("ARCHON_MCP_PORT", "8051")
                mcp_host = os.getenv("ARCHON_MCP_HOST", os.getenv("ARCHON_SERVER_HOST"))
                # Check for multiple Docker indicators
                is_docker = (
                    os.getenv("DOCKER_CONTAINER") == "true"
                    or os.getenv("DOCKER_ENV") == "true"
                    or Path("/.dockerenv").exists()
                )

                if mcp_host:
                    self.mcp_url = f"http://{mcp_host}:{mcp_port}"
                elif is_docker:
                    self.mcp_url = f"http://archon-mcp:{mcp_port}"
                else:
                    self.mcp_url = f"http://localhost:{mcp_port}"

        import os
        timeout_val = float(os.getenv("MCP_REQUEST_TIMEOUT", "30.0"))
        self.client = httpx.AsyncClient(timeout=timeout_val)
        logger.info(f"MCP Client initialized with URL: {self.mcp_url}, agent_type: {self.agent_type}, timeout: {timeout_val}s")

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def call_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """
        Call an MCP tool via HTTP.

        Args:
            tool_name: Name of the MCP tool to call
            **kwargs: Tool arguments

        Returns:
            The tool result (natural type)
        """
        try:
            # MCP tools are called via JSON-RPC protocol
            request_data = {"jsonrpc": "2.0", "method": tool_name, "params": kwargs, "id": 1}

            headers = {"Content-Type": "application/json"}
            if hasattr(self, "agent_type") and self.agent_type:
                headers["X-Agent-Type"] = self.agent_type

            # Make HTTP request to MCP server via the new /rpc bridge (Phase 4.6.19)
            response = await self.client.post(
                f"{self.mcp_url}/rpc",
                json=request_data,
                headers=headers,
            )

            response.raise_for_status()
            result = response.json()

            if "error" in result:
                error = result["error"]
                raise Exception(f"MCP tool error: {error.get('message', 'Unknown error')}")

            # Return the result part of the JSON-RPC response
            return result.get("result")

        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling MCP tool {tool_name}: {e}")
            raise Exception(f"Failed to call MCP tool: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            raise

    async def list_tools(self) -> list[MCPToolSchema]:
        """
        Dynamically list all registered MCP tools from the server.

        Returns:
            List of OpenAI-compatible tool schemas.
        """
        try:
            # list_tools is a special method handled by the /rpc fast path
            result = await self.call_tool("list_tools")
            if isinstance(result, list):
                parsed_tools = []
                for item in result:
                    if isinstance(item, dict):
                        if item.get("type") == "function" and "function" in item:
                            func_data = item["function"]
                            parsed_tools.append(MCPToolSchema(
                                name=func_data.get("name"),
                                description=func_data.get("description"),
                                inputSchema=func_data.get("parameters", {})
                            ))
                        else:
                            parsed_tools.append(MCPToolSchema(**item))
                return parsed_tools
            return []
        except Exception as e:
            logger.error(f"Failed to fetch tool list from MCP: {e}")
            return []

    # Convenience methods for common MCP tools

    async def perform_rag_query(self, query: str, source: str | None = None, match_count: int = 5) -> str:
        """Perform a RAG query through MCP."""
        result = await self.call_tool("perform_rag_query", query=query, source=source, match_count=match_count)
        return json.dumps(result) if isinstance(result, dict) else str(result)

    async def get_available_sources(self) -> str:
        """Get available sources through MCP."""
        result = await self.call_tool("get_available_sources")
        return json.dumps(result) if isinstance(result, dict) else str(result)

    async def search_code_examples(self, query: str, source_id: str | None = None, match_count: int = 5) -> str:
        """Search code examples through MCP."""
        result = await self.call_tool("search_code_examples", query=query, source_id=source_id, match_count=match_count)
        return json.dumps(result) if isinstance(result, dict) else str(result)

    async def manage_project(self, action: str, **kwargs) -> str:
        """Manage projects through MCP."""
        result = await self.call_tool("manage_project", action=action, **kwargs)
        return json.dumps(result) if isinstance(result, dict) else str(result)

    async def manage_document(self, action: str, project_id: str, **kwargs) -> str:
        """Manage documents through MCP."""
        result = await self.call_tool("manage_document", action=action, project_id=project_id, **kwargs)
        return json.dumps(result) if isinstance(result, dict) else str(result)

    async def manage_task(self, action: str, project_id: str, **kwargs) -> str:
        """Manage tasks through MCP."""
        result = await self.call_tool("manage_task", action=action, project_id=project_id, **kwargs)
        return json.dumps(result) if isinstance(result, dict) else str(result)


# Global MCP client instances by agent_type (created on first use)
_mcp_clients: dict[str, MCPClient] = {}


async def get_mcp_client(agent_type: str = "anonymous") -> MCPClient:
    """
    Get or create the global MCP client instance for a specific agent type.

    Args:
        agent_type: The role or identifier of the agent

    Returns:
        MCPClient instance
    """
    global _mcp_clients

    if agent_type not in _mcp_clients:
        _mcp_clients[agent_type] = MCPClient(agent_type=agent_type)

    return _mcp_clients[agent_type]
