"""
Project Schemas for API Requests and Responses
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    title: str
    description: str | None = None
    github_repo: str | None = None
    docs: list[Any] | None = None
    features: list[Any] | None = None
    data: list[Any] | None = None
    technical_sources: list[str] | None = None
    business_sources: list[str] | None = None
    pinned: bool | None = None


class UpdateProjectRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    github_repo: str | None = None
    docs: list[Any] | None = None
    features: list[Any] | None = None
    data: list[Any] | None = None
    technical_sources: list[str] | None = None
    business_sources: list[str] | None = None
    pinned: bool | None = None


class AssignableUser(BaseModel):
    id: str
    name: str
    role: str


class CreateTaskRequest(BaseModel):
    project_id: str
    title: str
    description: str | None = None
    status: str | None = "todo"
    priority: str | None = "medium"
    assignee: str | None = "User"
    assignee_id: str | None = None
    task_order: int | None = 0
    feature: str | None = None
    due_date: datetime | None = None
    knowledge_source_ids: list[str] | None = None
    is_recurring: bool | None = False
    crawler_target_id: str | None = None
    schedule_config: dict[str, Any] | None = None


class RefineTaskRequest(BaseModel):
    title: str
    description: str


class GenerateTaskFromAlertRequest(BaseModel):
    alert_id: str
    assignee_id: str | None = None


class Attachment(BaseModel):
    filename: str
    url: str


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee: str | None = None
    assignee_id: str | None = None
    task_order: int | None = None
    feature: str | None = None
    attachments: list[Attachment] | None = None
    due_date: datetime | None = None
    is_recurring: bool | None = None
    crawler_target_id: str | None = None
    schedule_config: dict[str, Any] | None = None


class AgentStatusUpdateRequest(BaseModel):
    status: str
    agent_id: str


class AgentOutputUpdateRequest(BaseModel):
    output: dict[str, Any]
    agent_id: str


class CreateDocumentRequest(BaseModel):
    document_type: str
    title: str
    content: dict[str, Any] | None = None
    tags: list[str] | None = None
    author: str | None = None


class UpdateDocumentRequest(BaseModel):
    title: str | None = None
    content: dict[str, Any] | None = None
    tags: list[str] | None = None
    author: str | None = None


class CreateVersionRequest(BaseModel):
    field_name: str
    content: dict[str, Any]
    change_summary: str | None = None
    change_type: str | None = "update"
    document_id: str | None = None
    created_by: str | None = "system"


class RestoreVersionRequest(BaseModel):
    restored_by: str | None = "system"
