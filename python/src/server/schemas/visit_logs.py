from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class VisitLogResponse(BaseModel):
    id: str | None = Field(default=None, description="Visit log ID")
    user_id: str | None = Field(default=None, description="User ID")
    customer_id: str | None = Field(default=None, description="Customer ID")
    lead_id: str | None = Field(default=None, description="Lead ID")
    latitude: float | None = Field(default=None, description="Latitude")
    longitude: float | None = Field(default=None, description="Longitude")
    location_address: str | None = Field(default=None, description="Location address")
    voice_transcript: str | None = Field(default=None, description="Voice transcript")
    summary: str | None = Field(default=None, description="AI summary")
    follow_up_tasks: list[str] | None = Field(default=None, description="Follow up tasks")
    audio_url: str | None = Field(default=None, description="Audio file URL")
    image_urls: list[str] | None = Field(default=None, description="Image URLs")
    created_at: str | datetime | None = Field(default=None, description="Created timestamp")
    updated_at: str | datetime | None = Field(default=None, description="Updated timestamp")
    visit_type: str | None = Field(default=None, description="Visit type")
    scheduling_recommendation: dict[str, Any] | None = Field(default=None, description="Dynamic scheduling recommendation")

class AttendanceStatusResponse(BaseModel):
    status: str | None = Field(default=None, description="Attendance status")
    clock_in_time: str | datetime | None = Field(default=None, description="Clock in time")
    id: str | None = Field(default=None, description="Attendance log ID")
    user_id: str | None = Field(default=None, description="User ID")
    clock_out_time: str | datetime | None = Field(default=None, description="Clock out time")
    latitude: float | None = Field(default=None, description="Latitude")
    longitude: float | None = Field(default=None, description="Longitude")
    location_name: str | None = Field(default=None, description="Location name")
    created_at: str | datetime | None = Field(default=None, description="Created timestamp")
    updated_at: str | datetime | None = Field(default=None, description="Updated timestamp")
