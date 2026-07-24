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


class VoiceProcessResult(BaseModel):
    """Pydantic model representing the parsed voice transcription and scheduling details."""

    transcript: str = Field(default="", description="語音逐字稿")
    summary: str = Field(default="音訊處理完成。", description="語音摘要")
    tasks: list[str] = Field(default_factory=list, description="跟進任務清單")
    scheduling_intent: bool = Field(default=False, description="是否提及下次預約會議時間的意圖")
    requested_date: str | None = Field(default=None, description="請求會議的日期 (YYYY-MM-DD)")
    requested_duration_hours: float = Field(default=1.0, description="請求會議預估時數 (小時)")
    meeting_topic: str | None = Field(default=None, description="會議討論主題與大綱")



class TimeSlot(BaseModel):
    start_time: datetime
    end_time: datetime


class SchedulingRecommendation(BaseModel):
    """Structured response returned by MarketBot/StatsService to the frontend."""

    meeting_topic: str
    suggested_slots: list[TimeSlot] = Field(default_factory=list, description="推薦的三個可行空檔選項")
    conflict_summary: str = Field(description="排除忙碌行程的簡短原因說明")


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
