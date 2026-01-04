from .job_tools import marketing_tools

def register_marketing_tools(mcp):
    """Register marketing tools with the MCP server."""
    for tool_cls in marketing_tools:
        mcp.tool()(tool_cls)
