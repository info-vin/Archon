from mcp.server.fastmcp import FastMCP

from .logo_tool import GenerateBrandAssetTool


def register_design_tools(mcp: FastMCP):
    """Register design-related tools with the MCP server."""

    @mcp.tool()
    async def generate_brand_asset(style: str = "eciton", format: str = "svg") -> str:
        """
        Generates a brand asset (logo) based on the specified style.

        Args:
            style: The visual style of the asset (default: "eciton").
                   "eciton" = Geometric Ant Node-Link style.
            format: The output format (default: "svg").

        Returns:
            The generated SVG code as a string.
        """
        tool = GenerateBrandAssetTool(style=style, format=format)
        return await tool.execute()
