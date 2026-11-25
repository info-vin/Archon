from typing import Any, Literal

from pydantic import BaseModel, Field

from src.server.services.shared_constants import TaskFeatureEnum, WorkflowStatusEnum


# --- 1. Shared State ---
class SharedState(BaseModel):
    messages: list[dict[str, Any]] = Field(default_factory=list)
    current_assignee: str | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    step_count: int = 0
    max_steps: int = 10  # Phase 5.4: Sufficient buffer for retries
    final_result: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    model_used: str | None = None
    task_type: str = TaskFeatureEnum.GENERAL.value  # Phase 5.0.2: Dynamic Prompt Governance
    conversation_id: str | None = None
    handoff_history: list[dict[str, str]] = Field(default_factory=list)
    status: str = WorkflowStatusEnum.RUNNING.value
    pending_approval_id: str | None = None


class SupervisorDecision(BaseModel):
    next_node: Literal["marketbot", "librarian", "summary", "devbot", "david", "end", "human", "bob"] = Field(
        description="The next agent to route to, or 'end' if task is completed, or 'human' if stuck."
    )
    reasoning: str = Field(description="Why this node was selected")
