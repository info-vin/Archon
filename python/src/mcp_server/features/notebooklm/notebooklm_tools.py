"""
NotebookLM integration tools for Archon MCP Server.
"""

import json
import logging

from mcp.server.fastmcp import Context, FastMCP

from notebooklm import NotebookLMClient

logger = logging.getLogger(__name__)


def register_notebooklm_tools(mcp: FastMCP):
    """Register NotebookLM integration tools with the MCP server."""

    # 1. Register the official complete tools from notebooklm-py
    try:
        from notebooklm.mcp.server import register_all

        register_all(mcp)
        logger.info("✓ Registered official notebooklm-py MCP tools")
    except Exception as e:
        logger.error(f"Failed to register official notebooklm-py tools: {e}")

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
