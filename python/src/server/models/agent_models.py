from typing import Any

from pydantic import BaseModel


class ExecutionStepResult(BaseModel):
    status: str
    checkpoint_id: str
    step_index: int
    message: str
    approval_id: str | None = None
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None

class ResumeExecutionResult(BaseModel):
    status: str
    conversation_id: str
    step_index: int
    message: str
    state_snapshot: dict[str, Any] | None = None
    agent_role: str | None = None
