from .job_tools import marketing_crawler_tools, marketing_tools


from mcp.server.fastmcp import FastMCP

def register_marketing_tools(mcp: FastMCP) -> None:
    """Register marketing tools with the MCP server."""
    for tool_cls in marketing_tools + marketing_crawler_tools:
        name = getattr(tool_cls, "tool_name", None)
        if name:
            mcp.tool(name=name)(tool_cls)
        else:
            mcp.tool()(tool_cls)
