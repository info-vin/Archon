from typing import Any

from pydantic import BaseModel, Field


class LogEntry(BaseModel):
    id: int | str
    source: str | None = None
    level: str | None = None
    message: str | None = None
    details: dict[str, Any] | None = None
    created_at: str | None = None
    project_name: str | None = None

class RecordGeminiLogResponse(BaseModel):
    log: LogEntry | None = Field(default=None, description="The created log entry data on success")
    error: str | None = Field(default=None, description="Error message if the logging failed")
