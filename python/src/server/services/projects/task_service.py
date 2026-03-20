"""
Task Service Module for Archon

This module provides core business logic for task operations that can be
shared between MCP tools and FastAPI endpoints.
"""

# Removed direct logging import - using unified config
import asyncio
from datetime import datetime
from typing import Any

from src.server.repositories.base_repository import BaseRepository
from src.server.utils import get_supabase_client

from ...config.logfire_config import get_logger
from ..shared_constants import AI_AGENT_ROLES  # Import AI_AGENT_ROLES from shared module

# agent_service will be imported locally within _notify_ai_agent_of_assignment to break circular dependency

logger = get_logger(__name__)

# Task updates are handled via polling - no broadcasting needed


class TaskService(BaseRepository):
    """Service class for task operations"""

    VALID_STATUSES = ["todo", "doing", "review", "done", "processing", "dispatched"]

    def __init__(self, supabase_client=None):
        """Initialize with optional supabase client"""
        client = supabase_client or get_supabase_client()
        super().__init__(client)

    def _notify_ai_agent_of_assignment(self, task_id: str, agent_id: str):
        """Delegates agent notification to maintenance submodule."""
        from .tasks.maintenance import notify_ai_agent_logic
        asyncio.create_task(notify_ai_agent_logic(task_id, agent_id))

    def validate_status(self, status: str) -> tuple[bool, str]:
        """Delegates status validation to maintenance submodule."""
        from .tasks.maintenance import validate_status_logic
        return validate_status_logic(status, self.VALID_STATUSES)

    def validate_assignee(self, assignee: str) -> tuple[bool, str]:
        """Delegates assignee validation to maintenance submodule."""
        from .tasks.maintenance import validate_assignee_logic
        return validate_assignee_logic(assignee)

    async def create_info_request_task(
        self,
        requester_id: str,
        subject: str,
        context: str,
        lead_id: str | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """
        Creates a specialized task for requesting information (Alice Loop).
        Flow: Bob requests -> Charlie Approves -> Alice executes.
        """
        try:
            # 1. Generate Description with AI (POBot) - Simplified for robustness
            # In a real scenario, this would call POBot to format the request nicely.
            # For now, we use a template to ensure reliability.
            description = (
                f"**Information Request**: {subject}\n\n"
                f"**Context**: {context}\n\n"
                f"**Action Required**: Please provide the missing information (e.g., Visit Logs, Client preferences).\n"
                f"**Requester**: {requester_id}\n"
            )
            if lead_id:
                description += f"**Related Lead**: {lead_id}"

            # 2. Create Task
            # Status: pending_approval (This effectively assigns it to Manager's queue)
            # Assignee: "Charlie" (Manager) for approval
            return await self.create_task(
                project_id="field_ops_001", # TODO: Defaults to Field Ops or a generic "Requests" project?
                title=f"Info Request: {subject}",
                description=description,
                assignee="Charlie", # Initial assignee is Manager for approval
                priority="high",
                feature="information_request",
                task_order=0
            )

        except Exception as e:
            logger.error(f"Error creating info request task: {e}")
            return False, {"error": str(e)}

    async def create_task(
        self,
        project_id: str,
        title: str,
        description: str = "",
        assignee: str = "User",
        task_order: int = 0,
        feature: str | None = None,
        sources: list[dict[str, Any]] | None = None,
        code_examples: list[dict[str, Any]] | None = None,
        due_date: datetime | None = None,
        knowledge_source_ids: list[str] | None = None,
        assignee_id: str | None = None,
        priority: str = "medium",
        is_recurring: bool = False,
        crawler_target_id: str | None = None,
        schedule_config: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Create a new task under a project with automatic reordering.

        Returns:
            Tuple of (success, result_dict)
        """
        try:
            # Validate inputs
            if not title or not isinstance(title, str) or len(title.strip()) == 0:
                return False, {"error": "Task title is required and must be a non-empty string"}

            if not project_id or not isinstance(project_id, str):
                return False, {"error": "Project ID is required and must be a string"}

            # Validate assignee
            is_valid, error_msg = self.validate_assignee(assignee)
            if not is_valid:
                return False, {"error": error_msg}

            task_status = "todo"

            # REORDERING LOGIC: If inserting at a specific position, increment existing tasks
            if task_order > 0:
                try:
                    # Get all tasks in the same project and status with task_order >= new task's order
                    existing_tasks_response = (
                        self.supabase_client.table("archon_tasks")
                        .select("id, task_order")
                        .eq("project_id", project_id)
                        .eq("status", task_status)
                        .gte("task_order", task_order)
                        .execute()
                    )

                    if existing_tasks_response.data:
                        logger.info(f"Reordering {len(existing_tasks_response.data)} existing tasks")

                        # Increment task_order for all affected tasks
                        for existing_task in existing_tasks_response.data:
                            self.supabase_client.table("archon_tasks").update({
                                "task_order": existing_task["task_order"] + 1,
                                "updated_at": datetime.now().isoformat(),
                            }).eq("id", existing_task["id"]).execute()
                except Exception as e:
                    logger.warning(f"Reordering tasks failed: {e}. Proceeding with task creation.")

            # Process knowledge_source_ids if provided
            final_sources = sources or []
            if knowledge_source_ids:
                for sid in knowledge_source_ids:
                    final_sources.append({"source_id": sid, "type": "knowledge_item"})

            task_data = {
                "project_id": project_id,
                "title": title,
                "description": description,
                "status": task_status,
                "assignee": assignee,
                "assignee_id": assignee_id,
                "task_order": task_order,
                "priority": priority,
                "sources": final_sources,
                "code_examples": code_examples or [],
                "is_recurring": is_recurring,
                "crawler_target_id": crawler_target_id,
                "schedule_config": schedule_config or {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            if feature:
                task_data["feature"] = feature

            if due_date:
                task_data["due_date"] = due_date.isoformat()

            def _create_query():
                return self.supabase_client.table("archon_tasks").insert(task_data).execute()

            success_create, create_result = self.execute_query(
                query_func=_create_query,
                error_context="Failed to create task"
            )

            if success_create:
                task = create_result["data"][0]

                # If the assignee is an AI agent, notify the MCP
                if assignee in AI_AGENT_ROLES:
                    self._notify_ai_agent_of_assignment(task_id=task["id"], agent_id=assignee)

                return True, {
                    "task": {
                        "id": task["id"],
                        "project_id": task["project_id"],
                        "title": task["title"],
                        "description": task["description"],
                        "status": task["status"],
                        "assignee": task["assignee"],
                        "assignee_id": task.get("assignee_id"),
                        "task_order": task["task_order"],
                        "priority": task.get("priority"),
                        "created_at": task["created_at"],
                        "due_date": task.get("due_date"),
                        "is_recurring": task.get("is_recurring"),
                        "crawler_target_id": task.get("crawler_target_id"),
                        "schedule_config": task.get("schedule_config"),
                    }
                }
            return False, create_result

        except Exception as e:
            logger.error(f"Error creating task: {e}")
            return False, {"error": f"Error creating task: {str(e)}"}

    async def list_tasks(
        self,
        project_id: str | None = None,
        status: str | None = None,
        include_closed: bool = False,
        exclude_large_fields: bool = False,
        include_archived: bool = False,
        assignee_id: str | None = None,
        assignee_name: str | None = None,
        include_unassigned: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        """
        List tasks with various filters. Delegates to query submodule.
        """
        from .tasks.query_logic import list_tasks_logic
        return await list_tasks_logic(
            self, project_id, status, include_closed, exclude_large_fields,
            include_archived, assignee_id, assignee_name, include_unassigned
        )

    async def get_task(self, task_id: str) -> tuple[bool, dict[str, Any]]:
        """
        Get a specific task by ID, including AI usage metrics (Phase 4.6.15).

        Returns:
            Tuple of (success, result_dict)
        """
        def _query():
            return self.supabase_client.table("archon_tasks").select("*").eq("id", task_id).execute()

        success, result = self.execute_query(
            query_func=_query,
            error_context=f"Task with ID {task_id} not found"
        )

        if not success:
            return False, result

        task_data = result["data"][0]

        # 1. Aggregate AI Metrics (Token Usage & Cost)
        try:
            # We search for token usage linked to this task_id.
            # AgentService logs usage with request_id containing the task_id.
            token_res = self.supabase_client.table("token_usage")\
                .select("total_tokens, cost_usd")\
                .ilike("request_id", f"%{task_id}%")\
                .execute()

            total_tokens = sum(row.get("total_tokens", 0) for row in (token_res.data or []))
            total_cost = sum(float(row.get("cost_usd", 0)) for row in (token_res.data or []))

            task_data["ai_metrics"] = {
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 6),
                "is_ai_powered": total_tokens > 0
            }
        except Exception as e:
            logger.warning(f"Failed to aggregate AI metrics for task {task_id}: {e}")
            task_data["ai_metrics"] = {"total_tokens": 0, "total_cost_usd": 0, "is_ai_powered": False}

        return True, {"task": task_data}

    async def update_task(
        self, task_id: str, update_fields: dict[str, Any]
    ) -> tuple[bool, dict[str, Any]]:
        """
        Update task with specified fields.

        Returns:
            Tuple of (success, result_dict)
        """
        try:
            # Get current task state to check for status change
            success, result = await self.get_task(task_id)
            if not success:
                return False, result
            current_task = result["task"]

            # Build update data
            update_data = {"updated_at": datetime.now().isoformat()}

            # Validate and add fields
            if "title" in update_fields:
                update_data["title"] = update_fields["title"]

            if "description" in update_fields:
                update_data["description"] = update_fields["description"]

            if "status" in update_fields:
                new_status = update_fields["status"]
                is_valid, error_msg = self.validate_status(new_status)
                if not is_valid:
                    return False, {"error": error_msg}
                update_data["status"] = new_status

                # If task is being marked as 'done', set completed_at timestamp
                if new_status == "done" and current_task.get("status") != "done":
                    update_data["completed_at"] = datetime.now().isoformat()
                # If task is being moved from 'done' to another status, clear completed_at
                elif new_status != "done" and current_task.get("status") == "done":
                    # Use a sentinel or handle this in the update dict to satisfy MyPy
                    update_data["completed_at"] = ""  # Using empty string as sentinel for null in JSONB update if needed, or cast to Any
                    # Actually, for Supabase/Postgrest via Python wrapper, None works but MyPy might complain if the dict type isn't Any
                    update_data["completed_at"] = None  # type: ignore

            if "assignee" in update_fields:
                is_valid, error_msg = self.validate_assignee(update_fields["assignee"])
                if not is_valid:
                    return False, {"error": error_msg}
                update_data["assignee"] = update_fields["assignee"]

            if "assignee_id" in update_fields:
                update_data["assignee_id"] = update_fields["assignee_id"]

            if "task_order" in update_fields:
                update_data["task_order"] = update_fields["task_order"]

            if "feature" in update_fields:
                update_data["feature"] = update_fields["feature"]

            if "attachments" in update_fields:
                update_data["attachments"] = update_fields["attachments"]

            if "due_date" in update_fields:
                # Ensure datetime is serialized to string for Supabase
                due_val = update_fields["due_date"]
                if hasattr(due_val, 'isoformat'):
                    update_data["due_date"] = due_val.isoformat()
                else:
                    update_data["due_date"] = due_val

            if "priority" in update_fields:
                update_data["priority"] = update_fields["priority"]

            if "is_recurring" in update_fields:
                update_data["is_recurring"] = update_fields["is_recurring"]

            if "crawler_target_id" in update_fields:
                update_data["crawler_target_id"] = update_fields["crawler_target_id"]

            if "schedule_config" in update_fields:
                update_data["schedule_config"] = update_fields["schedule_config"]

            if "completed_at" in update_fields:
                comp_val = update_fields["completed_at"]
                if hasattr(comp_val, 'isoformat'):
                    update_data["completed_at"] = comp_val.isoformat()
                else:
                    update_data["completed_at"] = comp_val

            # Update task
            def _update_query():
                return (
                    self.supabase_client.table("archon_tasks")
                    .update(update_data)
                    .eq("id", task_id)
                    .execute()
                )

            success_update, update_result = self.execute_query(
                query_func=_update_query,
                error_context=f"Task with ID {task_id} not found"
            )

            if success_update:
                task = update_result["data"][0]

                # If the assignee was updated to an AI agent, notify the MCP
                if "assignee" in update_fields and update_fields["assignee"] in AI_AGENT_ROLES:
                    self._notify_ai_agent_of_assignment(
                        task_id=task_id, agent_id=update_fields["assignee"]
                    )

                return True, {"task": task, "message": "Task updated successfully"}
            return False, update_result

        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False, {"error": f"Error updating task: {str(e)}"}

    async def archive_task(
        self, task_id: str, archived_by: str = "mcp"
    ) -> tuple[bool, dict[str, Any]]:
        """Archives a task. Delegates to maintenance submodule."""
        from .tasks.maintenance import archive_task_logic
        return await archive_task_logic(self, task_id, archived_by)

    async def update_task_status_from_agent(
        self, task_id: str, new_status: str, agent_id: str
    ) -> tuple[bool, dict[str, Any]]:
        """Updates status via agent. Delegates to maintenance submodule."""
        from .tasks.maintenance import update_task_status_from_agent_logic
        return await update_task_status_from_agent_logic(self, task_id, new_status, agent_id)

    async def save_agent_output(
        self, task_id: str, output: dict[str, Any], agent_id: str
    ) -> tuple[bool, dict[str, Any]]:
        """Saves agent output. Delegates to maintenance submodule."""
        from .tasks.maintenance import save_agent_output_logic
        return await save_agent_output_logic(self, task_id, output, agent_id)

    async def refine_task_description(self, title: str, description: str) -> str:
        """
        Uses POBot (RAG-enhanced) to transform a raw description into
        a structured product spec.
        """
        from .tasks.ai_operations import refine_task_description_logic
        return await refine_task_description_logic(self.supabase_client, title, description)

    async def get_all_project_task_counts(self) -> tuple[bool, dict[str, dict[str, int]]]:
        """
        Get task counts for all projects. Delegates to query submodule.
        """
        from .tasks.query_logic import get_all_project_task_counts_logic
        return await get_all_project_task_counts_logic(self)

    async def generate_task_from_alert(
        self,
        alert_id: str,
        assignee_id: str | None = None,
        triggered_by: str | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """
        AI-powered task generation from a Sentinel alert.
        Delegates to AI submodule.
        """
        from .tasks.ai_operations import generate_task_from_alert_logic
        return await generate_task_from_alert_logic(self, alert_id, assignee_id)

    async def prune_archived_tasks(self, days_old: int = 30) -> tuple[bool, dict[str, Any]]:
        """Prunes old archived tasks. Delegates to maintenance submodule."""
        from .tasks.maintenance import prune_archived_tasks_logic
        return await prune_archived_tasks_logic(self, days_old)


task_service = TaskService()
