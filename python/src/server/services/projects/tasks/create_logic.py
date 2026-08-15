"""
Create Logic Submodule for Task Service
"""

from datetime import datetime
from typing import Any, cast

from src.server.config.logfire_config import get_logger

logger = get_logger(__name__)


async def create_info_request_task_logic(
    task_service_instance, requester_id: str, subject: str, context: str, lead_id: str | None = None
) -> tuple[bool, dict[str, Any]]:
    """
    Creates a specialized task for requesting information (Alice Loop).
    Flow: Bob requests -> Charlie Approves -> Alice executes.
    """
    try:
        # 1. Generate Description with AI (POBot) - Simplified for robustness
        description = (
            f"**Information Request**: {subject}\n\n"
            f"**Context**: {context}\n\n"
            f"**Action Required**: Please provide the missing information (e.g., Visit Logs, Client preferences).\n"
            f"**Requester**: {requester_id}\n"
        )
        if lead_id:
            description += f"**Related Lead**: {lead_id}"

        # 2. Get Project ID Dynamically (Phase 4.6.23 Hardening)
        from src.server.schemas.settings import ProjectConfig
        from src.server.services.settings_service import SettingsService

        settings = SettingsService(task_service_instance.supabase_client)
        try:
            config = ProjectConfig.model_validate(settings.get_all_settings())
        except Exception:
            config = ProjectConfig()
        project_id = config.default_business_project

        # Fallback logic: if no setting, find the first available project
        if not project_id:
            logger.warning("No 'default_business_project' set. Falling back to the first available project.")

            p_query = task_service_instance.supabase_client.table("archon_projects").select("id").limit(1)

            p_success, p_result = task_service_instance.execute_query(
                p_query, "Get fallback project", require_data=True
            )
            if p_success and p_result["data"]:
                project_id = p_result["data"][0]["id"]
            else:
                project_id = "field_ops_001"  # Ultimate safety fallback

        # 3. Create Task
        return cast(
            tuple[bool, dict[str, Any]],
            await task_service_instance.create_task(
                project_id=project_id,
                title=f"Info Request: {subject}",
                description=description,
                assignee="Charlie",  # Initial assignee is Manager for approval
                priority="high",
                feature="information_request",
                task_order=0,
            ),
        )

    except Exception as e:
        logger.error(f"Error creating info request task: {e}")
        return False, {"error": str(e)}


async def create_task_logic(
    task_service_instance,
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
    collaborator_agent_ids: list[str] | None = None,
    priority: str = "medium",
    is_recurring: bool = False,
    crawler_target_id: str | None = None,
    schedule_config: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any]]:
    """
    Create a new task under a project with automatic reordering.
    """
    try:
        # Validate inputs
        if not title or not isinstance(title, str) or len(title.strip()) == 0:
            return False, {"error": "Task title is required and must be a non-empty string"}

        if not project_id or not isinstance(project_id, str):
            return False, {"error": "Project ID is required and must be a string"}

        # SSOT/DRY: Auto-resolve assignee name from assignee_id if it's the default 'User'
        if assignee == "User" and assignee_id:
            from src.server.services.shared_constants import AI_AGENT_ROLES
            for name, uuid in AI_AGENT_ROLES.items():
                if uuid == assignee_id:
                    assignee = name
                    break

        # Validate assignee
        is_valid, error_msg = task_service_instance.validate_assignee(assignee)
        if not is_valid:
            return False, {"error": error_msg}

        task_status = "todo"

        # REORDERING LOGIC: If inserting at a specific position, increment existing tasks
        if task_order > 0:
            try:
                success, rpc_res = task_service_instance.execute_query(
                    task_service_instance.supabase_client.rpc(
                        "increment_task_orders",
                        {
                            "p_project_id": project_id,
                            "p_status": task_status,
                            "p_start_order": task_order,
                        },
                    ),
                    error_context="Reordering tasks failed via RPC"
                )
                if not success:
                    raise Exception(rpc_res.get("error", "Unknown RPC error"))
                logger.info(f"Reordered tasks in project {project_id} starting from order {task_order}")
            except Exception as e:
                logger.warning(f"Reordering tasks failed via RPC: {e}. Proceeding with task creation.")

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

        create_query = task_service_instance.supabase_client.table("archon_tasks").insert(task_data)

        success_create, create_result = task_service_instance.execute_query(
            query_func=create_query, error_context="Failed to create task"
        )

        if success_create:
            task = create_result["data"][0]

            # If the assignee is an AI agent (by ID or prefix), notify the MCP
            agent_id = None
            if assignee_id in AI_AGENT_ROLES.values():
                agent_id = assignee_id
            else:
                for name, aid in AI_AGENT_ROLES.items():
                    if assignee and (name.startswith(assignee) or assignee in name):
                        agent_id = aid
                        break

            if agent_id:
                task_service_instance._notify_ai_agent_of_assignment(task_id=task["id"], agent_id=agent_id)

            return True, {
                "task": {
                    "id": task["id"],
                    "project_id": task["project_id"],
                    "title": task["title"],
                    "description": task["description"],
                    "status": task["status"],
                    "assignee": task["assignee"],
                    "assignee_id": task.get("assignee_id"),
                    "collaborator_agent_ids": task.get("collaborator_agent_ids", []),
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
