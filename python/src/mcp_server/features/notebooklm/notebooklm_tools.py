
"""
NotebookLM integration tools for Archon MCP Server.
"""

import json
import logging
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from notebooklm import NotebookLMClient

logger = logging.getLogger(__name__)


def register_notebooklm_tools(mcp: FastMCP) -> None:
    """Register NotebookLM integration tools with the MCP server."""

    # 1. Register the official complete tools from notebooklm-py
    # [MONKEY PATCH] fastmcp 1.12.x enforces strict Pydantic core schemas and @tool() syntax.
    # We dynamically patch ToolResult and the mcp.tool decorator before importing notebooklm.
    import fastmcp.tools.tool
    from pydantic_core import core_schema

    class _ToolResultPydanticPatch:
        @classmethod
        def __get_pydantic_core_schema__(cls, source_type: Any, handler: Any) -> Any:
            return core_schema.any_schema()

    if not hasattr(fastmcp.tools.tool.ToolResult, "__get_pydantic_core_schema__"):
        fastmcp.tools.tool.ToolResult.__get_pydantic_core_schema__ = _ToolResultPydanticPatch.__get_pydantic_core_schema__  # type: ignore

    original_tool = mcp.tool

    def patched_tool(*args: Any, **kwargs: Any) -> Any:
        if len(args) == 1 and callable(args[0]) and not kwargs:
            # Called as @mcp.tool (without parenthesis)
            return original_tool()(args[0])
        else:
            return original_tool(*args, **kwargs)

    mcp.tool = patched_tool  # type: ignore

    from notebooklm.mcp.server import register_all

    register_all(mcp)  # type: ignore[arg-type]
    logger.info("✓ Registered official notebooklm-py MCP tools (Monkey patched)")

    # Restore the original decorator to prevent side-effects on other tools
    mcp.tool = original_tool  # type: ignore

    # 2. Register explicit names requested by the plan for exact compatibility
    @mcp.tool()
    async def notebooklm_list_notebooks(ctx: Context) -> str:
        """List all notebooks in NotebookLM."""
        client: NotebookLMClient = ctx.request_context.lifespan_context.client
        if not client:
            return json.dumps(
                {"success": False, "error": "NotebookLMClient not initialized. Please verify credentials."}
            )

        try:
            notebooks = await client.notebooks.list()
            return json.dumps(
                {
                    "success": True,
                    "notebooks": [
                        {
                            "id": nb.id,
                            "title": nb.title,
                            "sources_count": nb.sources_count,
                            "created_at": str(nb.created_at) if nb.created_at else None,
                        }
                        for nb in notebooks
                    ],
                },
                indent=2,
            )
        except Exception as e:
            logger.error(f"Error in notebooklm_list_notebooks: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool()
    async def notebooklm_create_notebook(ctx: Context, title: str) -> str:
        """Create a new notebook with a title."""
        client: NotebookLMClient = ctx.request_context.lifespan_context.client
        if not client:
            return json.dumps(
                {"success": False, "error": "NotebookLMClient not initialized. Please verify credentials."}
            )

        try:
            nb = await client.notebooks.create(title)
            return json.dumps(
                {
                    "success": True,
                    "notebook_id": nb.id,
                    "title": nb.title,
                    "message": f"Notebook '{title}' created successfully.",
                },
                indent=2,
            )
        except Exception as e:
            logger.error(f"Error in notebooklm_create_notebook: {e}")
            return json.dumps({"success": False, "error": str(e)})

    @mcp.tool()
    async def notebooklm_ask_question(ctx: Context, notebook_id: str, question: str) -> str:
        """Ask a question to the sources in a specific notebook."""
        client: NotebookLMClient = ctx.request_context.lifespan_context.client
        if not client:
            return json.dumps(
                {"success": False, "error": "NotebookLMClient not initialized. Please verify credentials."}
            )

        try:
            res = await client.chat.ask(notebook_id, question)
            return json.dumps(
                {
                    "success": True,
                    "answer": res.answer if hasattr(res, "answer") else str(res),
                    "conversation_id": res.conversation_id if hasattr(res, "conversation_id") else None,
                },
                indent=2,
            )
        except Exception as e:
            logger.error(f"Error in notebooklm_ask_question: {e}")
            return json.dumps({"success": False, "error": str(e)})
