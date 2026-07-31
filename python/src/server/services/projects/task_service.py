"""
Task Service Module for Archon

This module provides core business logic for task operations that can be
shared between MCP tools and FastAPI endpoints.
"""

import asyncio
from datetime import datetime
from typing import Any

from src.server.repositories.base_repository import BaseRepository
from src.server.utils import get_supabase_client

from ...config.logfire_config import get_logger
from ..shared_constants import TaskStatusEnum

logger = get_logger(__name__)


class TaskService(BaseRepository):
    """Service class for task operations"""

    VALID_STATUSES: list[str] = [
        TaskStatusEnum.TODO.value,
        TaskStatusEnum.DOING.value,
        TaskStatusEnum.REVIEW.value,
        TaskStatusEnum.DONE.value,
        TaskStatusEnum.PROCESSING.value,
        TaskStatusEnum.DISPATCHED.value,
    ]

    def __init__(self, supabase_client: Any = None) -> None:
        """Initialize with optional supabase client"""
        client = supabase_client or get_supabase_client()
        super().__init__(client)

    def _notify_ai_agent_of_assignment(self, task_id: str, agent_id: str):
        from .tasks.maintenance import notify_ai_agent_logic

        asyncio.create_task(notify_ai_agent_logic(task_id, agent_id))

    def validate_status(self, status: str) -> tuple[bool, str]:
        from .tasks.maintenance import validate_status_logic

        return validate_status_logic(status, self.VALID_STATUSES)

    def validate_assignee(self, assignee: str) -> tuple[bool, str]:
        from .tasks.maintenance import validate_assignee_logic

        return validate_assignee_logic(assignee)

    async def create_info_request_task(
        self, requester_id: str, subject: str, context: str, lead_id: str | None = None
    ) -> tuple[bool, dict[str, Any]]:
        from .tasks.create_logic import create_info_request_task_logic

        return await create_info_request_task_logic(self, requester_id, subject, context, lead_id)

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
        collaborator_agent_ids: list[str] | None = None,
        priority: str = "medium",
        is_recurring: bool = False,
        crawler_target_id: str | None = None,
        schedule_config: dict[str, Any] | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        from .tasks.create_logic import create_task_logic

        return await create_task_logic(
            self,
            project_id,
            title,
            description,
            assignee,
            task_order,
            feature,
            sources,
            code_examples,
            due_date,
            knowledge_source_ids,
            assignee_id,
            collaborator_agent_ids,
            priority,
            is_recurring,
            crawler_target_id,
            schedule_config,
        )

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
        from .tasks.query_logic import list_tasks_logic

        return await list_tasks_logic(
            self,
            project_id,
            status,
            include_closed,
            exclude_large_fields,
            include_archived,
            assignee_id,
            assignee_name,
            include_unassigned,
        )

    async def get_task(self, task_id: str) -> tuple[bool, dict[str, Any]]:
        from .tasks.query_logic import get_task_logic

        return await get_task_logic(self, task_id)

    async def update_task(self, task_id: str, update_fields: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        from .tasks.update_logic import update_task_logic

        return await update_task_logic(self, task_id, update_fields)

    async def archive_task(self, task_id: str, archived_by: str = "mcp") -> tuple[bool, dict[str, Any]]:
        from .tasks.maintenance import archive_task_logic

        return await archive_task_logic(self, task_id, archived_by)

    async def update_task_status_from_agent(
        self, task_id: str, new_status: str, agent_id: str
    ) -> tuple[bool, dict[str, Any]]:
        from .tasks.maintenance import update_task_status_from_agent_logic

        return await update_task_status_from_agent_logic(self, task_id, new_status, agent_id)

    async def save_agent_output(
        self, task_id: str, output: dict[str, Any], agent_id: str
    ) -> tuple[bool, dict[str, Any]]:
        from .tasks.maintenance import save_agent_output_logic

        return await save_agent_output_logic(self, task_id, output, agent_id)

    async def refine_task_description(self, title: str, description: str) -> str:
        from .tasks.ai_operations import refine_task_description_logic

        return await refine_task_description_logic(self.supabase_client, title, description)

    async def get_all_project_task_counts(self) -> tuple[bool, dict[str, dict[str, int]]]:
        from .tasks.query_logic import get_all_project_task_counts_logic

        return await get_all_project_task_counts_logic(self)

    async def generate_task_from_alert(
        self, alert_id: str, assignee_id: str | None = None, triggered_by: str | None = None
    ) -> tuple[bool, dict[str, Any]]:
        from .tasks.ai_operations import generate_task_from_alert_logic

        return await generate_task_from_alert_logic(self, alert_id, assignee_id)

    async def prune_archived_tasks(self, days_old: int = 30) -> tuple[bool, dict[str, Any]]:
        from .tasks.maintenance import prune_archived_tasks_logic

        return await prune_archived_tasks_logic(self, days_old)


task_service = TaskService()
