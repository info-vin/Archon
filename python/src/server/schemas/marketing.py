from datetime import datetime
from typing import Any
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


class CombinedSourceResponse(BaseModel):
    id: str | UUID | None = Field(default=None, description="Source ID")
    type: str | None = Field(default=None, description="Type of source (lead, task, blog)")
    title: str | None = Field(default=None, description="Display title or company name")
    score: int | float = Field(default=0, description="Relevance or AI score")
    summary: str = Field(default="", description="Short summary or excerpt")
    date: datetime | str | None = Field(default=None, description="Creation timestamp")
    status: str | None = Field(default=None, description="Workflow status (for blogs)")
    name: str | None = Field(default=None, description="Optional legacy alias for source name")
    source_type: str | None = Field(default=None, description="Optional legacy alias for source type")

    model_config = {
        "from_attributes": True
    }


class ContentContextResponse(BaseModel):
    source_id: str = Field(description="ID of the source")
    source_type: str = Field(description="Type of the source")
    rag_refs: list[dict[str, Any]] = Field(default_factory=list, description="RAG references retrieved for context")
    context_summary: str = Field(default="", description="Summary text of the context")

    model_config = {
        "from_attributes": True
    }


class ManagerAlertResponse(BaseModel):
    id: str | None = Field(default=None, description="Unique alert ID")
    level: str | None = Field(default=None, description="Alert level (e.g., ALERT, INFO)")
    source: str | None = Field(default=None, description="System source of the alert")
    message: str | None = Field(default=None, description="Alert message body")
    created_at: str | None = Field(default=None, description="Timestamp when alert was raised")
    details: dict[str, Any] | None = Field(default=None, description="Additional context metadata")

    model_config = {
        "from_attributes": True
    }


class MarketingTrendsResponse(BaseModel):
    keyword_growth: list[dict[str, Any]] = Field(default_factory=list, description="Keyword growth trend series")
    sankey_flow: dict[str, Any] = Field(default_factory=dict, description="Sankey conversion flow graph data")
    weekly_leads: list[int] = Field(default_factory=list, description="Optional weekly lead acquisition counts")
    top_industries: list[str] = Field(default_factory=list, description="Optional top active industries")

    model_config = {
        "from_attributes": True
    }


class MarketingIntelligenceResponse(BaseModel):
    total_leads: int = Field(default=0, description="Total number of leads analysed")
    funnel: dict[str, int] = Field(default_factory=dict, description="Funnel stage counts")
    distribution: dict[str, int] = Field(default_factory=dict, description="Industry/Role category distribution")
    metrics: dict[str, Any] = Field(default_factory=dict, description="Key performance metrics")
    timestamp: str | None = Field(default=None, description="Timestamp of calculation")
    error: str | None = Field(default=None, description="Error message if calculation failed")

    model_config = {
        "from_attributes": True
    }


class KnowledgeSeedResponse(BaseModel):
    status: str | None = Field(default=None, description="Seeding status")
    scanned_dir: str | None = Field(default=None, description="Directory scanned for knowledge files")
    total_files: int | None = Field(default=None, description="Total markdown/text files discovered")
    indexed_count: int | None = Field(default=None, description="Number of files successfully indexed")
    errors: list[str] = Field(default_factory=list, description="List of per-file indexing errors")
    items_seeded: int | None = Field(default=None, description="Optional alias for number of items seeded")
    message: str | None = Field(default=None, description="Descriptive result message")
    error: str | None = Field(default=None, description="Error details if seeding failed")

    model_config = {
        "from_attributes": True
    }


class PendingApprovalsResponse(BaseModel):
    blogs: list[dict[str, Any]] = Field(default_factory=list, description="Pending blog posts awaiting review")
    leads: list[dict[str, Any]] = Field(default_factory=list, description="Pending leads awaiting review")

    model_config = {
        "from_attributes": True
    }


class MarketingStatsResponse(BaseModel):
    total_leads: int = Field(default=0, description="Total number of leads")
    total_blog_posts: int = Field(default=0, description="Total number of blog posts")
    conversion_rate: float = Field(default=0.0, description="Lead conversion rate percentage")
    active_campaigns: int = Field(default=0, description="Number of active campaigns")
    last_updated: str | None = Field(default=None, description="ISO timestamp of last update")
    error: str | None = Field(default=None, description="Error message if stat calculation failed")

    model_config = {
        "from_attributes": True
    }


class SentinelRunResponse(BaseModel):
    status: str = Field(description="Status of sentinel scan trigger")
    message: str = Field(description="Information message regarding sentinel scan execution")

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


class VendorResponse(BaseModel):
    id: str | UUID = Field(description="Unique identifier for the vendor")
    name: str = Field(description="Name of the vendor")
    contact_email: str | None = Field(default=None, description="Contact email of the vendor")
    description: str | None = Field(default=None, description="Description or notes for the vendor")
    status: str = Field(description="Vendor status")
    owner_id: str | UUID | None = Field(default=None, description="Owner ID of the vendor")

    model_config = {
        "from_attributes": True
    }


class PromoteLeadResponse(BaseModel):
    vendor: VendorResponse = Field(description="The created vendor object from promoting the lead")


class ApprovalRequest(BaseModel):
    notes: str | None = None


class RejectSuggestionRequest(BaseModel):
    item_type: str
    item_id: str


class DraftBlogRequest(BaseModel):
    topic: str
    industry: list[str] | None = None
    keywords: str | None = None


class DraftBlogResponse(BaseModel):
    title: str = Field(description="Title of the drafted blog post")
    content: str = Field(description="Full text content of the blog post")
    excerpt: str | None = Field(default="", description="Short excerpt or summary of the post")
    status: str | None = Field(default="review", description="Publication or workflow status of the post")

    model_config = {
        "from_attributes": True
    }


class DraftFromLeadsRequest(BaseModel):
    lead_ids: list[str]


class DraftFromLeadsResponse(BaseModel):
    task_id: str = Field(description="Unique identifier of the created background task")
    status: str = Field(description="Task dispatch status")


class ResetLeadsResponse(BaseModel):
    success: bool = Field(description="Indicates whether leads reset succeeded")


class ApprovalActionResponse(BaseModel):
    success: bool = Field(description="Indicates whether the approval processing action succeeded")


class SubmitBlogResponse(BaseModel):
    status: str | None = Field(default=None, description="Status of submission")
    ai_score: int | None = Field(default=None, description="Calculated AI quality score")
    post_id: str | None = Field(default=None, description="Post ID submitted")
    error: str | None = Field(default=None, description="Error message if submission failed")

    model_config = {
        "from_attributes": True
    }


class LogoResponse(BaseModel):
    status: str = Field(description="Status of visual asset generation")
    image_url: str = Field(description="URL or data string of generated image/logo")
    tier: str = Field(description="Generation tier used (native, physical_svg, emergency)")
    svg_content: str | None = Field(default=None, description="Raw SVG content if generated")

    model_config = {
        "from_attributes": True
    }


class RejectSuggestionResponse(BaseModel):
    notes: str = Field(description="Suggested feedback or rejection notes")

    model_config = {
        "from_attributes": True
    }


class JobResponse(BaseModel):
    title: str = Field(description="Title of the job posting")
    company: str = Field(description="Company name offering the position")
    location: str | None = Field(default=None, description="Job location")
    salary: str | None = Field(default=None, description="Salary information")
    url: str | None = Field(default=None, description="URL of the job posting")
    description: str | None = Field(default=None, description="Short job description")
    description_full: str | None = Field(default=None, description="Full job description")
    skills: list[str] | None = Field(default=None, description="List of required skills")
    source: str = Field(default="104", description="Source platform of the job posting")
    company_website: str | None = Field(default=None, description="Company website URL")
    keyword: str | None = Field(default=None, description="Search keyword used")
    identified_need: str | None = Field(default=None, description="Identified need or pain point")
    real_id: str | None = Field(default=None, description="Original source job ID")

    model_config = {
        "from_attributes": True
    }
