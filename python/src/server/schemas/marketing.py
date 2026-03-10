
from pydantic import BaseModel, Field


class PitchRequest(BaseModel):
    job_title: str
    company: str
    description: str

class PitchResponse(BaseModel):
    content: str
    references: list[str]

class CreateLeadRequest(BaseModel):
    company_name: str
    job_title: str
    source: str = "manual"
    source_job_url: str | None = None
    identified_need: str | None = None
    status: str = "new"
    pitch_content: str | None = None

class PromoteLeadRequest(BaseModel):
    vendor_name: str
    contact_email: str | None = None
    notes: str | None = None

class DraftBlogRequest(BaseModel):
    topic: str
    keywords: str | None = None
    tone: str = "professional"
    context_source_id: str | None = None
    context_type: str | None = "lead"
    industry: list[str] | None = None
    style: list[str] | None = None
    length: str = "standard"
    charts: list[str] | None = None
    enable_web_research: bool = False

class DraftBlogResponse(BaseModel):
    title: str
    content: str
    excerpt: str
    references: list[str] = []
    used_prompt: str | None = None
    metadata: dict | None = None

class ApprovalActionRequest(BaseModel):
    review_notes: str | None = Field(None, alias='reviewNotes')
    model_config = {"populate_by_name": True}

class MarketingRejectSuggestionRequest(BaseModel):
    blog_post_id: str

class RequestInfoRequest(BaseModel):
    subject: str
    context: str
    lead_id: str | None = None

class LeadUpdate(BaseModel):
    status: str | None = None
    enrichment_score: int | None = None
    identified_need: str | None = None
    lost_reason: str | None = None
    lost_competitor: str | None = None

class LogoRequest(BaseModel):
    style: str = "eciton"
    primary_color: str | None = None

class DispatchAlertRequest(BaseModel):
    assignee_id: str | None = None
