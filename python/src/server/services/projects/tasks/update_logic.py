"""
Update Logic Submodule for Task Service
"""

from datetime import datetime
from typing import Any

from src.server.config.logfire_config import get_logger
from src.server.services.shared_constants import AI_AGENT_ROLES

logger = get_logger(__name__)

async def update_task_logic(
    task_service_instance, task_id: str, update_fields: dict[str, Any]
) -> tuple[bool, dict[str, Any]]:
    """
    Update task with specified fields.
    """
    try:
        # Get current task state to check for status change
        success, result = await task_service_instance.get_task(task_id)
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
            is_valid, error_msg = task_service_instance.validate_status(new_status)
            if not is_valid:
                return False, {"error": error_msg}
            update_data["status"] = new_status

            # If task is being marked as 'done', set completed_at timestamp
            if new_status == "done" and current_task.get("status") != "done":
                update_data["completed_at"] = datetime.now().isoformat()
            # If task is being moved from 'done' to another status, clear completed_at
            elif new_status != "done" and current_task.get("status") == "done":
                update_data["completed_at"] = None  # type: ignore

        if "assignee" in update_fields:
            is_valid, error_msg = task_service_instance.validate_assignee(update_fields["assignee"])
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
            if hasattr(due_val, "isoformat"):
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
            if hasattr(comp_val, "isoformat"):
                update_data["completed_at"] = comp_val.isoformat()
            else:
                update_data["completed_at"] = comp_val

        # Update task
        def _update_query():
            return task_service_instance.supabase_client.table("archon_tasks").update(update_data).eq("id", task_id).execute()

        success_update, update_result = task_service_instance.execute_query(
            query_func=_update_query, error_context=f"Task with ID {task_id} not found"
        )

        if success_update:
            task = update_result["data"][0]

            # If the assignee was updated to an AI agent, notify the MCP
            if "assignee" in update_fields and update_fields["assignee"] in AI_AGENT_ROLES:
                task_service_instance._notify_ai_agent_of_assignment(task_id=task_id, agent_id=update_fields["assignee"])

            return True, {"task": task, "message": "Task updated successfully"}
        return False, update_result

    except Exception as e:
        logger.error(f"Error updating task: {e}")
        return False, {"error": f"Error updating task: {str(e)}"}
