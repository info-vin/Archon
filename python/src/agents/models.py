from typing import Any
from pydantic import BaseModel

class AgentRequest(BaseModel):
    agent_type: str
    prompt: str
    context: dict[str, Any] | None = None
    options: dict[str, Any] | None = None

class AgentResponse(BaseModel):
    success: bool
    result: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None

class WorkflowRequest(BaseModel):
    prompt: str
    context: dict[str, Any] | None = None

class RootResponse(BaseModel):
    status: str
    service: str

class HealthResponse(BaseModel):
    status: str
    service: str
    agents_available: list[str]
    note: str

class AgentInfo(BaseModel):
    name: str
    model: str
    description: str
    available: bool

class AgentListResponse(BaseModel):
    agents: dict[str, AgentInfo]
    total: int
