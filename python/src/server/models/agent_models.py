from typing import Any

from pydantic import BaseModel, Field


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


class ApprovalRequestResponse(BaseModel):
    approval_id: str | None = Field(description="Unique ID of the pending approval request")
    conversation_id: str = Field(description="Associated conversation ID")
    checkpoint_id: str = Field(description="Associated checkpoint ID")
    tool_name: str = Field(description="Name of the sensitive tool requested")
    tool_args: dict[str, Any] = Field(description="Arguments for the tool call")
    risk_level: str = Field(description="Risk level, typically HIGH")
    status: str = Field(description="Status of the approval, e.g., PENDING")
    created_at: str | None = Field(description="Timestamp when the request was created")
    expires_at: str | None = Field(description="Timestamp when the request expires")


class ReviewApprovalResponse(BaseModel):
    success: bool = Field(description="Whether the review was successfully processed")
    approval_id: str | None = Field(description="The reviewed approval ID")
    status: str = Field(description="The new status of the approval, e.g., APPROVED or REJECTED")
    message: str = Field(description="Result message of the review action")


class AgentCheckpointResponse(BaseModel):
    id: str | None = Field(description="Unique ID of the checkpoint")
    conversation_id: str = Field(description="Associated conversation ID")
    step_index: int = Field(description="Execution step index")
    agent_role: str = Field(description="Role of the agent during this step")
    status: str = Field(description="Status of the agent step")
    state_snapshot: dict[str, Any] = Field(description="Complete state snapshot at this checkpoint")
    last_tool_call: dict[str, Any] | None = Field(description="The last tool call made before this checkpoint")
    created_at: str | None = Field(description="Timestamp when the checkpoint was created")


class AgentHealthResponse(BaseModel):
    status: str = Field(..., description="Health status of the service")
    service: str = Field(..., description="Name of the service")


class AssignableAgentResponse(BaseModel):
    id: str = Field(..., description="Unique identifier or UUID of the agent")
    name: str = Field(..., description="Display name or role name of the agent")
    role: str = Field(..., description="Role designation of the agent")
    tools: list[str] = Field(default_factory=list, description="List of tool names assigned to the agent")
    description: str = Field(default="AI Agent", description="Brief description or prompt summary of the agent")
