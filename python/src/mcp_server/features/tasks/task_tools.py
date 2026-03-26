"""
Consolidated task management tools for Archon MCP Server.

Reduces the number of individual CRUD operations while maintaining full functionality.
"""

import json
import logging
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

from ...utils.error_handling import MCPErrorFormatter
from ...utils.http_client import call_api

logger = logging.getLogger(__name__)

# Optimization constants
MAX_DESCRIPTION_LENGTH = 1000
DEFAULT_PAGE_SIZE = 10


def truncate_text(text: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
    """Truncate text to maximum length with ellipsis."""
    if text and len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def optimize_task_response(task: dict) -> dict:
    """Optimize task object for MCP response."""
    task = task.copy()

    # Truncate description if present
    if "description" in task and task["description"]:
        task["description"] = truncate_text(task["description"])

    # Replace arrays with counts
    if "sources" in task and isinstance(task["sources"], list):
        task["sources_count"] = len(task["sources"])
        del task["sources"]

    if "code_examples" in task and isinstance(task["code_examples"], list):
        task["code_examples_count"] = len(task["code_examples"])
        del task["code_examples"]

    return task


def register_task_tools(mcp: FastMCP):
    """Register consolidated task management tools with the MCP server."""

    @mcp.tool()
    async def find_tasks(
        ctx: Context,
        query: str | None = None,
        task_id: str | None = None,
        filter_by: str | None = None,
        filter_value: str | None = None,
        project_id: str | None = None,
        include_closed: bool = True,
        page: int = 1,
        per_page: int = DEFAULT_PAGE_SIZE,
    ) -> str:
        """
        Find and search tasks (consolidated: list + search + get).
        """
        try:
            # Single task get mode
            if task_id:
                result = await call_api("GET", f"/api/tasks/{task_id}")
                if result.get("success"):
                    # Remove 'success' from result before wrapping in task
                    result.pop("success")
                    return json.dumps({"success": True, "task": result})

                # Special handling for 404
                if "HTTP 404" in str(result.get("error")):
                    return MCPErrorFormatter.format_error(
                        error_type="not_found",
                        message=f"Task {task_id} not found",
                        suggestion="Verify the task ID is correct",
                        http_status=404,
                    )
                return json.dumps(result, indent=2)

            # List mode with search and filters
            params: dict[str, Any] = {
                "page": page,
                "per_page": per_page,
                "exclude_large_fields": True,
            }

            if query:
                params["q"] = query

            path = "/api/tasks"
            if filter_by == "project" and filter_value:
                path = f"/api/projects/{filter_value}/tasks"
                params["include_archived"] = False
            elif filter_by == "status" and filter_value:
                params["status"] = filter_value
                params["include_closed"] = include_closed
                if project_id:
                    params["project_id"] = project_id
            elif filter_by == "assignee" and filter_value:
                params["assignee"] = filter_value
                params["include_closed"] = include_closed
                if project_id:
                    params["project_id"] = project_id
            elif project_id:
                params["project_id"] = project_id
                params["include_closed"] = include_closed
            else:
                params["include_closed"] = include_closed

            result = await call_api("GET", path, params=params)

            if not result.get("success"):
                return json.dumps(result, indent=2)

            # Extract tasks from result
            tasks = []
            total_count = 0

            if "tasks" in result:
                tasks = result["tasks"]
                total_count = result.get("total_count", len(tasks))
            elif "data" in result:
                tasks = result["data"]
                total_count = result.get("total", len(tasks))
            elif isinstance(result.get("result"), list): # Compatibility
                tasks = result["result"]
                total_count = len(tasks)

            # Optimize task responses
            optimized_tasks = [optimize_task_response(task) for task in tasks]

            return json.dumps({
                "success": True,
                "tasks": optimized_tasks,
                "total_count": total_count,
                "count": len(optimized_tasks),
                "query": query,
            })

        except Exception as e:
            logger.error(f"Error listing tasks: {e}", exc_info=True)
            return MCPErrorFormatter.from_exception(e, "list tasks")

    @mcp.tool()
    async def manage_task(
        ctx: Context,
        action: str,
        task_id: str | None = None,
        project_id: str | None = None,
        title: str | None = None,
        description: str | None = None,
        status: str | None = None,
        assignee: str | None = None,
        task_order: int | None = None,
        feature: str | None = None
    ) -> str:
        """
        Manage tasks (consolidated: create/update/delete).
        """
        try:
            if action == "create":
                if not project_id or not title:
                    return MCPErrorFormatter.format_error("validation_error", "project_id and title required for create")

                result = await call_api("POST", "/api/tasks", json={
                    "project_id": project_id,
                    "title": title,
                    "description": description or "",
                    "assignee": assignee or "User",
                    "task_order": task_order or 0,
                    "feature": feature,
                    "sources": [],
                    "code_examples": [],
                })

                if result.get("success"):
                    task = result.get("task")
                    if task:
                        task = optimize_task_response(task)
                    return json.dumps({
                        "success": True,
                        "task": task,
                        "task_id": task.get("id") if task else None,
                        "message": result.get("message", "Task created successfully"),
                    })
                return json.dumps(result, indent=2)

            elif action == "update":
                if not task_id:
                    return MCPErrorFormatter.format_error("validation_error", "task_id required for update")

                update_fields = {k: v for k, v in {
                    "title": title, "description": description, "status": status,
                    "assignee": assignee, "task_order": task_order, "feature": feature
                }.items() if v is not None}

                if not update_fields:
                    return MCPErrorFormatter.format_error("validation_error", "No fields to update")

                result = await call_api("PUT", f"/api/tasks/{task_id}", json=update_fields)

                if result.get("success"):
                    task = result.get("task")
                    if task:
                        task = optimize_task_response(task)
                    return json.dumps({
                        "success": True,
                        "task": task,
                        "message": result.get("message", "Task updated successfully"),
                    })
                return json.dumps(result, indent=2)

            elif action == "delete":
                if not task_id:
                    return MCPErrorFormatter.format_error("validation_error", "task_id required for delete")

                result = await call_api("DELETE", f"/api/tasks/{task_id}")
                return json.dumps(result, indent=2)

            return MCPErrorFormatter.format_error("invalid_action", f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error managing task ({action}): {e}", exc_info=True)
            return MCPErrorFormatter.from_exception(e, f"{action} task")

    @mcp.tool()
    async def report_task_status(ctx: Context, task_id: str, status: str, agent_id: str) -> str:
        """Allows an AI agent to report a status update for a specific task."""
        result = await call_api("POST", f"/api/tasks/{task_id}/agent-status", json={"status": status, "agent_id": agent_id})
        return json.dumps(result, indent=2)

    @mcp.tool()
    async def report_task_output(ctx: Context, task_id: str, output: dict[str, Any], agent_id: str) -> str:
        """Allows an AI agent to report its final output or intermediate results for a specific task."""
        result = await call_api("POST", f"/api/tasks/{task_id}/agent-output", json={"output": output, "agent_id": agent_id})
        return json.dumps(result, indent=2)
