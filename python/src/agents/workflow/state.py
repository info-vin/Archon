from typing import Any, Literal

from pydantic import BaseModel, Field


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
    task_type: str = "General"  # Phase 5.0.2: Dynamic Prompt Governance


class SupervisorDecision(BaseModel):
    next_node: Literal["marketbot", "librarian", "summary", "devbot", "david", "end", "human"] = Field(
        description="The next agent to route to, or 'end' if task is completed, or 'human' if stuck."
    )
    reasoning: str = Field(description="Why this node was selected")
