from mcp.server.fastmcp import FastMCP

from .execution_tools import developer_execution_tools
from .file_operation_tools import developer_file_tools
from .version_control_tools import developer_version_control_tools


def register_developer_tools(mcp: FastMCP):
    """Register all developer tools with the MCP server."""

    # Register file operation tools
    for file_tool_cls in developer_file_tools:
        mcp.add_tool(file_tool_cls)

    # Register version control tools
    for vc_tool_cls in developer_version_control_tools:
        mcp.add_tool(vc_tool_cls)

    # Register execution tools
    for exec_tool_cls in developer_execution_tools:
        mcp.add_tool(exec_tool_cls)
