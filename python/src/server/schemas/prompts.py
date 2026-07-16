from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PromptMetadata(BaseModel):
    group: str | None = None
    subgroup: str | None = None
    target_file: str | None = None
    theme: str | None = None

    class Config:
        extra = "allow"

class PromptResponse(BaseModel):
    id: str | None = None
    prompt_name: str
    prompt: str
    description: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    is_system_protected: bool = False
    category: str = "SYSTEM_AGENT"
    metadata: dict[str, Any] = Field(default_factory=dict)

class PromptUpdateRequest(BaseModel):
    content: str | None = None
    prompt: str | None = None
    description: str | None = None
    category: str | None = None
    metadata: dict[str, Any] | None = None
