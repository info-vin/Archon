"""
Pydantic Schemas for Agent Outputs and JSONB Validation (Phase 5.1.0)
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class LogDetailsSchema(BaseModel):
    """Schema for archon_logs.details JSONB field"""

    request_id: str | None = None
    task_id: str | None = None
    agent_id: str | None = None
    strategy: str | None = None
    execution_time_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GroupChatOutputSchema(BaseModel):
    """Schema for Supervisor / Group Chat structured output"""

    summary: str
    decisions: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    raw_responses: dict[str, Any] = Field(default_factory=dict)
    model_used: str | None = None


class AgentOutputSchema(BaseModel):
    """
    Schema for individual entries in archon_tasks.attachments (JSONB list)
    """

    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    output_type: Literal["text", "structured", "group_chat"] = "text"
    output: str | dict[str, Any] | GroupChatOutputSchema
    metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic config for serialization"""

        json_encoders = {datetime: lambda v: v.isoformat()}
