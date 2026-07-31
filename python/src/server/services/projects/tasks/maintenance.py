"""
Maintenance and State Submodule for Task Service (Phase 4.6.12 Hardening)

This module handles task validation, AI agent notifications,
archiving, and maintenance tasks like pruning.
"""

from datetime import datetime, timedelta
from typing import Any, Literal, cast

from src.server.config.logfire_config import get_logger
from src.server.schemas.agent_outputs import AgentOutputSchema

logger = get_logger(__name__)


def validate_status_logic(status: str, valid_statuses: list[str]) -> tuple[bool, str]:
    """Validate task status against allowed list"""
    if status not in valid_statuses:
        return (
            False,
            f"Invalid status '{status}'. Must be one of: {', '.join(valid_statuses)}",
        )
    return True, ""


def validate_assignee_logic(assignee: str) -> tuple[bool, str]:
    """Validate task assignee consistency"""
    if not assignee or not isinstance(assignee, str) or len(assignee.strip()) == 0:
        return False, "Assignee must be a non-empty string"
    return True, ""


async def notify_ai_agent_logic(task_id: str, agent_id: str):
    """
    Triggers the agent service call in a non-blocking way.
    """
    try:
        from src.server.services.agent_service import agent_service

        logger.info(f"Scheduling notification for AI agent {agent_id} for task {task_id}")
        await agent_service.run_agent_task(task_id=task_id, agent_id=agent_id)
    except Exception as e:
        logger.error(f"Failed to notify agent {agent_id}: {e}")


async def archive_task_logic(
    task_service_instance, task_id: str, archived_by: str = "mcp"
) -> tuple[bool, dict[str, Any]]:
    """
    Archive a task and all its subtasks (soft delete).
    """
    try:
        success_get, get_result = await task_service_instance.get_task(task_id)
        if not success_get:
            return False, cast(dict[str, Any], get_result)

        task = get_result["task"]
        if task.get("archived") is True:
            return False, {"error": f"Task with ID {task_id} is already archived"}

        archive_data = {
            "archived": True,
            "archived_at": datetime.now().isoformat(),
            "archived_by": archived_by,
            "updated_at": datetime.now().isoformat(),
        }

        def _archive_query() -> Any:
            return (
                task_service_instance.supabase_client.table("archon_tasks")
                .update(archive_data)
                .eq("id", task_id)
                .execute()
            )

        success_archive, archive_result = task_service_instance.execute_query(
            query_func=_archive_query, error_context=f"Failed to archive task {task_id}"
        )

        if success_archive:
            return True, {"task_id": task_id, "message": "Task archived successfully"}
        return False, cast(dict[str, Any], archive_result)

    except Exception as e:
        logger.error(f"Error archiving task logic: {e}")
        return False, {"error": str(e)}


async def prune_archived_tasks_logic(task_service_instance, days_old: int = 30) -> tuple[bool, dict[str, Any]]:
    """
    Permanently delete archived tasks older than X days.
    """
    try:
        cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
        logger.info(f"Pruning archived tasks older than {days_old} days (cutoff: {cutoff_date})")

        tasks_to_prune = (
            task_service_instance.supabase_client.table("archon_tasks")
            .select("id")
            .eq("archived", True)
            .lt("archived_at", cutoff_date)
            .execute()
        )

        count = len(tasks_to_prune.data) if tasks_to_prune.data else 0

        if count > 0:
            task_service_instance.supabase_client.table("archon_tasks").delete().eq("archived", True).lt(
                "archived_at", cutoff_date
            ).execute()
            logger.info(f"Successfully pruned {count} tasks")

        return True, {"pruned_count": count, "cutoff_date": cutoff_date}
    except Exception as e:
        logger.error(f"Error pruning tasks logic: {e}")
        return False, {"error": str(e)}


async def update_task_status_from_agent_logic(
    task_service_instance, task_id: str, new_status: str, agent_id: str
) -> tuple[bool, dict[str, Any]]:
    """
    Update a task's status from an agent with authority validation.
    """
    try:
        success, result = await task_service_instance.get_task(task_id)
        if not success:
            return False, cast(dict[str, Any], result)
        current_task = result["task"]

        if current_task.get("assignee") != agent_id:
            error_msg = f"Agent '{agent_id}' is not authorized to update task '{task_id}'. Assigned to '{current_task.get('assignee')}'."
            logger.warning(error_msg)
            return False, {"error": error_msg}

        return cast(
            tuple[bool, dict[str, Any]],
            await task_service_instance.update_task(task_id, {"status": new_status, "assignee": agent_id}),
        )
    except Exception as e:
        logger.error(f"Error updating task status from agent logic: {e}")
        return False, {"error": str(e)}


async def save_agent_output_logic(
    task_service_instance, task_id: str, output: dict[str, Any], agent_id: str
) -> tuple[bool, dict[str, Any]]:
    """
    Save the output from an AI agent to the task's attachments.
    """
    try:
        success, result = await task_service_instance.get_task(task_id)
        if not success:
            return False, cast(dict[str, Any], result)
        current_task = result["task"]

        if current_task.get("assignee") != agent_id:
            error_msg = f"Agent '{agent_id}' is not authorized to save output for task '{task_id}'."
            logger.warning(error_msg)
            return False, {"error": error_msg}

        # Phase 5.1.0: Pydantic Boundary Validation
        try:
            # Determine output type based on content structure
            output_type = "text"
            if isinstance(output, dict):
                output_type = "group_chat" if "summary" in output and "decisions" in output else "structured"

            validated_output = AgentOutputSchema(
                agent_id=agent_id,
                timestamp=datetime.now(),
                output_type=cast(Literal["text", "structured", "group_chat"], output_type), # 合法
                output=output,
            )
            # Convert to dict for JSONB storage
            agent_output_data = validated_output.model_dump(mode="json")
        except Exception as ve:
            logger.error(f"Validation failed for agent output: {ve}")
            # Fallback to legacy format but log error
            agent_output_data = {"agent_id": agent_id, "timestamp": datetime.now().isoformat(), "output": output}

        current_attachments = current_task.get("attachments") or []
        if isinstance(current_attachments, list):
            current_attachments.append(agent_output_data)
            new_attachments = current_attachments
        else:
            new_attachments = [current_attachments, agent_output_data]

        return cast(
            tuple[bool, dict[str, Any]],
            await task_service_instance.update_task(task_id, {"attachments": new_attachments}),
        )
    except Exception as e:
        logger.error(f"Error saving agent output logic: {e}")
        return False, {"error": str(e)}
