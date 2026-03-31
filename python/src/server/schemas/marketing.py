from pydantic import BaseModel


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


class DraftBlogRequest(BaseModel):
    topic: str
    industry: list[str] | None = None
    keywords: str | None = None
