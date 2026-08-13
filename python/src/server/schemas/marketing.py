from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class LeadResponse(BaseModel):
    id: UUID = Field(description="Unique identifier for the lead")
    company_name: str = Field(description="Name of the company")
    source_job_url: str | None = Field(default=None, description="URL of the job posting that sourced this lead")
    status: str | None = Field(default=None, description="Current status of the lead")
    identified_need: str | None = Field(default=None, description="Identified need or pain point")
    assigned_sales_id: UUID | None = Field(default=None, description="ID of the assigned sales representative")
    created_at: datetime | str | None = Field(default=None, description="Timestamp of lead creation")
    updated_at: datetime | str | None = Field(default=None, description="Timestamp of last update")
    job_title: str | None = Field(default=None, description="Job title associated with the lead")
    description_snippet: str | None = Field(default=None, description="Snippet of the description")
    contact_name: str | None = Field(default=None, description="Name of the contact person")
    contact_email: str | None = Field(default=None, description="Email of the contact person")
    contact_phone: str | None = Field(default=None, description="Phone number of the contact person")
    linked_project_id: UUID | None = Field(default=None, description="ID of the linked project")
    last_contacted_at: datetime | str | None = Field(default=None, description="Timestamp of last contact")
    next_followup_date: datetime | str | None = Field(default=None, description="Scheduled date for next followup")
    company_website: str | None = Field(default=None, description="Company website URL")
    enrichment_status: str | None = Field(default=None, description="Status of lead enrichment")
    enrichment_score: int | None = Field(default=None, description="Score indicating lead quality")
    last_enriched_at: datetime | str | None = Field(default=None, description="Timestamp of last enrichment")
    auto_archived_reason: str | None = Field(default=None, description="Reason for automatic archiving")
    email: str | None = Field(default=None, description="General email associated with the lead")
    source: str | None = Field(default=None, description="Source of the lead")
    pitch_content: str | None = Field(default=None, description="Content of the pitch")
    lost_reason: str | None = Field(default=None, description="Reason for losing the lead")
    lost_competitor: str | None = Field(default=None, description="Competitor who won the lost lead")
    tenant_id: UUID | None = Field(default=None, description="Tenant ID")

    model_config = {
        "from_attributes": True
    }


class LeadActionResponse(BaseModel):
    lead: LeadResponse = Field(description="The created or updated lead object")


class PitchRequest(BaseModel):
    company: str
    job_title: str


class PitchResponse(BaseModel):
    content: str
    references: list[str] = []


class LogoRequest(BaseModel):
    style: str


class LeadCreateRequest(BaseModel):
    company_name: str
    contact_name: str | None = None
    email: str | None = None
    identified_need: str | None = None
    source_job_url: str | None = None


class LeadUpdateRequest(BaseModel):
    status: str | None = None
    identified_need: str | None = None
    pitch_content: str | None = None


class PromoteLeadRequest(BaseModel):
    vendor_name: str
    email: str | None = None
    notes: str | None = None


class ApprovalRequest(BaseModel):
    notes: str | None = None


class RejectSuggestionRequest(BaseModel):
    item_type: str
    item_id: str


class DraftBlogRequest(BaseModel):
    topic: str
    industry: list[str] | None = None
    keywords: str | None = None


class DraftFromLeadsRequest(BaseModel):
    lead_ids: list[str]
