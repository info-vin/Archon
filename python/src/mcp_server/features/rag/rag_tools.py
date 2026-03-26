"""
RAG Module for Archon MCP Server (HTTP-based version)

This module provides tools for:
- RAG query and search
- Source management
- Code example extraction and search

This version uses HTTP calls to the server service instead of importing
service modules directly, enabling true microservices architecture.
"""

import json
import logging
import os

from mcp.server.fastmcp import Context, FastMCP

from ...utils.http_client import call_api

logger = logging.getLogger(__name__)


def get_setting(key: str, default: str = "false") -> str:
    """Get a setting from environment variable."""
    return os.getenv(key, default)


def get_bool_setting(key: str, default: bool = False) -> bool:
    """Get a boolean setting from environment variable."""
    value = get_setting(key, "false" if not default else "true")
    return value.lower() in ("true", "1", "yes", "on")


def register_rag_tools(mcp: FastMCP):
    """Register all RAG tools with the MCP server."""

    @mcp.tool()
    async def rag_get_available_sources(ctx: Context) -> str:
        """
        Get list of available sources in the knowledge base.

        Returns:
            JSON string with structure:
            - success: bool - Operation success status
            - sources: list[dict] - Array of source objects
            - count: int - Number of sources
            - error: str - Error description if success=false
        """
        result = await call_api("GET", "/api/rag/sources")
        if result.get("success"):
            sources = result.get("sources", [])
            return json.dumps(
                {"success": True, "sources": sources, "count": len(sources)}, indent=2
            )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def rag_search_knowledge_base(
        ctx: Context,
        query: str,
        source_id: str | None = None,
        match_count: int = 5,
        return_mode: str = "pages"
    ) -> str:
        """
        Search knowledge base for relevant content using RAG.

        Args:
            query: Search query - Keep it SHORT and FOCUSED (2-5 keywords).
            source_id: Optional source ID filter from rag_get_available_sources().
            match_count: Max results (default: 5)
            return_mode: "pages" (default) or "chunks"

        Returns:
            JSON string with success status and search results.
        """
        request_data = {
            "query": query,
            "match_count": match_count,
            "return_mode": return_mode
        }
        if source_id:
            request_data["source"] = source_id

        result = await call_api("POST", "/api/rag/query", json=request_data)

        if result.get("success"):
            return json.dumps(
                {
                    "success": True,
                    "results": result.get("results", []),
                    "return_mode": result.get("return_mode", return_mode),
                    "reranked": result.get("reranked", False),
                    "error": None,
                },
                indent=2,
            )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def rag_search_code_examples(
        ctx: Context, query: str, source_id: str | None = None, match_count: int = 5
    ) -> str:
        """
        Search for relevant code examples in the knowledge base.

        Args:
            query: Search query - Keep it SHORT and FOCUSED (2-5 keywords).
            source_id: Optional source ID filter.
            match_count: Max results (default: 5)

        Returns:
            JSON string with code example results.
        """
        request_data = {"query": query, "match_count": match_count}
        if source_id:
            request_data["source"] = source_id

        result = await call_api("POST", "/api/rag/code-examples", json=request_data)

        if result.get("success"):
            return json.dumps(
                {
                    "success": True,
                    "results": result.get("results", []),
                    "reranked": result.get("reranked", False),
                    "error": None,
                },
                indent=2,
            )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def rag_list_pages_for_source(
        ctx: Context, source_id: str, section: str | None = None
    ) -> str:
        """
        List all pages for a given knowledge source.

        Args:
            source_id: Source ID (e.g., "src_1234abcd")
            section: Optional filter for section title
        """
        params = {"source_id": source_id}
        if section:
            params["section"] = section

        result = await call_api("GET", "/api/pages", params=params)

        if result.get("success"):
            return json.dumps(
                {
                    "success": True,
                    "pages": result.get("pages", []),
                    "total": result.get("total", 0),
                    "source_id": result.get("source_id", source_id),
                    "error": None,
                },
                indent=2,
            )
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def rag_read_full_page(
        ctx: Context, page_id: str | None = None, url: str | None = None
    ) -> str:
        """
        Retrieve full page content from knowledge base.

        Args:
            page_id: Page UUID (e.g., "550e8400-e29b-41d4-a716-446655440000")
            url: Page URL
        """
        if not page_id and not url:
            return json.dumps({"success": False, "error": "Must provide either page_id or url"}, indent=2)

        if page_id:
            result = await call_api("GET", f"/api/pages/{page_id}")
        else:
            result = await call_api("GET", "/api/pages/by-url", params={"url": url})

        if result.get("success"):
            # Unwrap redundant 'success' from call_api if needed, but result already has it
            # The backend returns page data directly if success
            return json.dumps(result, indent=2)
        return json.dumps(result, indent=2)

    # Log successful registration
    logger.info("✓ RAG tools registered (HTTP-based version)")
