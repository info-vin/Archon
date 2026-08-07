"""
Query Logic Submodule for Task Service (Phase 4.6.12 Hardening)

This module handles complex task listing with RBAC filters and
batch project task counting.
"""

from typing import Any, cast

from src.server.config.logfire_config import get_logger
from src.server.schemas.agent_outputs import AgentOutputSchema

from ...shared_constants import TaskStatusEnum

logger = get_logger(__name__)


async def list_tasks_logic(
    task_service_instance,
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
    List tasks with various filters including RBAC and unassigned visibility.
    """
    try:
        # Start with base query
        if exclude_large_fields:
            query = task_service_instance.supabase_client.table("archon_tasks").select( # 合法
                "id, project_id, parent_task_id, title, description, "
                "status, assignee, assignee_id, collaborator_agent_ids, task_order, feature, archived, "
                "archived_at, archived_by, created_at, updated_at, due_date, "
                "sources, code_examples, is_recurring, crawler_target_id, schedule_config, retry_count"
            )
        else:
            query = task_service_instance.supabase_client.table("archon_tasks").select("* ") # 合法

        filters_applied = []

        # Apply filters
        if assignee_id:
            if include_unassigned:
                # Fix FB-03: Show tasks assigned to me OR unassigned
                query = query.or_(f"assignee_id.eq.{assignee_id},assignee_id.is.null")
                filters_applied.append(f"assignee_id={assignee_id} OR unassigned")
            else:
                query = query.eq("assignee_id", assignee_id)
                filters_applied.append(f"assignee_id={assignee_id}")

        if assignee_name and not assignee_id:
            if include_unassigned:
                query = query.or_(f"assignee.eq.{assignee_name},assignee.eq.User")
                filters_applied.append(f"assignee={assignee_name} OR User")
            else:
                query = query.eq("assignee", assignee_name)
                filters_applied.append(f"assignee={assignee_name}")

        if status:
            is_valid, error_msg = task_service_instance.validate_status(status)
            if not is_valid:
                return False, {"error": error_msg}
            query = query.eq("status", status)
            filters_applied.append(f"status={status}")
        elif not include_closed:
            query = query.neq("status", "done")
            filters_applied.append("exclude done tasks")

        if not include_archived:
            query = query.or_("archived.is.null,archived.is.false")
            filters_applied.append("exclude archived tasks")

        logger.debug(f"Listing tasks with filters: {', '.join(filters_applied)}")

        response = query.order("task_order", desc=False).order("created_at", desc=False).execute()

        tasks = []
        for task in response.data:
            task_data = {
                "id": task["id"],
                "project_id": task["project_id"],
                "title": task["title"],
                "description": task["description"],
                "status": task["status"],
                "assignee": task.get("assignee", "User"),
                "assignee_id": task.get("assignee_id"),
                "task_order": task.get("task_order", 0),
                "feature": task.get("feature"),
                "priority": task.get("priority", "medium"),
                "created_at": task["created_at"],
                "updated_at": task["updated_at"],
                "archived": task.get("archived", False),
                "due_date": task.get("due_date"),
                "is_recurring": task.get("is_recurring"),
                "crawler_target_id": task.get("crawler_target_id"),
                "schedule_config": task.get("schedule_config"),
            }

            if not exclude_large_fields:
                raw_attachments = task.get("attachments", [])
                validated_attachments = []
                latest_agent_output = None
                if isinstance(raw_attachments, list):
                    for att in raw_attachments:
                        try:
                            # Try to validate and normalize
                            val_att = AgentOutputSchema.model_validate(att).model_dump(mode="json")
                            validated_attachments.append(val_att)
                            latest_agent_output = val_att.get("output")
                        except Exception:
                            # Fallback for legacy data
                            validated_attachments.append(att)
                            if isinstance(att, dict) and "output" in att:
                                latest_agent_output = att.get("output")
                task_data["attachments"] = validated_attachments
                if latest_agent_output is not None:
                    task_data["agent_output"] = latest_agent_output
                task_data["sources"] = task.get("sources", [])
                task_data["code_examples"] = task.get("code_examples", [])
            else:
                task_data["stats"] = {
                    "sources_count": len(task.get("sources", [])),
                    "code_examples_count": len(task.get("code_examples", [])),
                }
            tasks.append(task_data)

        filter_info = []
        if project_id:
            filter_info.append(f"project_id={project_id}")
        if status:
            filter_info.append(f"status={status}")
        if not include_closed:
            filter_info.append("excluding closed tasks")

        return True, {
            "tasks": tasks,
            "total_count": len(tasks),
            "filters_applied": ", ".join(filter_info) if filter_info else "none",
            "include_closed": include_closed,
        }

    except Exception as e:
        logger.error(f"Error listing tasks logic: {e}")
        return False, {"error": f"Error listing tasks: {str(e)}"}


async def get_all_project_task_counts_logic(task_service_instance) -> tuple[bool, dict[str, dict[str, int]]]:
    """
    Get task counts for all projects in a single optimized query.
    """
    try:
        logger.debug("Fetching task counts for all projects in batch")
        response = (
            task_service_instance.supabase_client.table("archon_tasks") # 合法
            .select("project_id, status")
            .or_("archived.is.null,archived.is.false")
            .execute()
        )

        if not response.data:
            return True, {}

        counts_by_project: dict[str, dict[str, int]] = {}
        for task in response.data:
            project_id = task.get("project_id")
            status = task.get("status")
            if not project_id or not status:
                continue

            if project_id not in counts_by_project:
                counts_by_project[project_id] = {"todo": 0, "doing": 0, "done": 0}

            if status == TaskStatusEnum.REVIEW:
                counts_by_project[project_id][TaskStatusEnum.DOING] += 1
            elif status in [TaskStatusEnum.TODO, TaskStatusEnum.DOING, TaskStatusEnum.DONE]:
                counts_by_project[project_id][status] += 1

        return True, counts_by_project
    except Exception as e:
        logger.error(f"Error fetching task counts logic: {e}")
        error_data: Any = {"error": f"Error fetching task counts: {str(e)}"}
        return False, cast(dict[str, dict[str, int]], error_data)


async def get_task_logic(task_service_instance, task_id: str) -> tuple[bool, dict[str, Any]]:
    """
    Get a specific task by ID, including AI usage metrics.
    """

    query = task_service_instance.supabase_client.table("archon_tasks").select("*").eq("id", task_id) # 合法

    success, result = task_service_instance.execute_query(
        query_func=query, error_context=f"Task with ID {task_id} not found"
    )

    if not success:
        return False, result

    task_data = result["data"][0]

    # Phase 5.1.0: Transform JSONB attachments to Pydantic objects
    raw_attachments = task_data.get("attachments", [])
    validated_attachments = []
    latest_agent_output = None
    if isinstance(raw_attachments, list):
        for att in raw_attachments:
            try:
                val_att = AgentOutputSchema.model_validate(att).model_dump(mode="json")
                validated_attachments.append(val_att)
                latest_agent_output = val_att.get("output")
            except Exception:
                validated_attachments.append(att)
                if isinstance(att, dict) and "output" in att:
                    latest_agent_output = att.get("output")
    task_data["attachments"] = validated_attachments
    if latest_agent_output is not None:
        task_data["agent_output"] = latest_agent_output

    # 1. Aggregate AI Metrics (Token Usage & Cost)
    try:
        # We search for token usage linked to this task_id.
        token_res = (
            task_service_instance.supabase_client.table("token_usage") # 合法
            .select("total_tokens, cost_usd")
            .ilike("request_id", f"%{task_id}%")
            .execute()
        )

        total_tokens = 0
        total_cost = 0.0
        for row in token_res.data or []:
            total_tokens += row.get("total_tokens", 0)
            total_cost += float(row.get("cost_usd", 0))

        task_data["ai_metrics"] = {
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "is_ai_powered": total_tokens > 0,
        }
    except Exception as e:
        logger.warning(f"Failed to aggregate AI metrics for task {task_id}: {e}")
        task_data["ai_metrics"] = {"total_tokens": 0, "total_cost_usd": 0, "is_ai_powered": False}

    return True, {"task": task_data}
