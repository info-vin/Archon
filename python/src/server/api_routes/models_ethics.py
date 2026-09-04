from datetime import datetime

from pydantic import BaseModel, Field


class EthicsEvent(BaseModel):
    id: str = Field(description="Unique identifier for the ethics event")
    severity: str = Field(description="Severity level of the ethics event (e.g., info, warning, critical)")
    event_type: str = Field(description="Type of ethics event")
    description: str | None = Field(default=None, description="Detailed description of the ethics event")
    raw_input: str | None = Field(default=None, description="Raw input text or prompt that triggered the event")
    created_at: datetime = Field(description="Timestamp when the event occurred")
