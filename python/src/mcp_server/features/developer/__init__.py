from mcp.server.fastmcp import FastMCP

from .execution_tools import developer_execution_tools
from .file_operation_tools import developer_file_tools
from .version_control_tools import developer_version_control_tools


def register_developer_tools(mcp: FastMCP):
    """Register all developer tools with the MCP server."""

    # Register file operation tools
    for file_tool_cls in developer_file_tools:
        name = getattr(file_tool_cls, "tool_name", None)
        if name:
            mcp.tool(name=name)(file_tool_cls)
        else:
            mcp.add_tool(file_tool_cls)

    # Register version control tools
    for vc_tool_cls in developer_version_control_tools:
        name = getattr(vc_tool_cls, "tool_name", None)
        if name:
            mcp.tool(name=name)(vc_tool_cls)
        else:
            mcp.add_tool(vc_tool_cls)

    # Register execution tools
    for exec_tool_cls in developer_execution_tools:
        name = getattr(exec_tool_cls, "tool_name", None)
        if name:
            mcp.tool(name=name)(exec_tool_cls)
        else:
            mcp.add_tool(exec_tool_cls)
