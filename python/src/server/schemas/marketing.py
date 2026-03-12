from pydantic import BaseModel
from typing import List, Optional

class PitchRequest(BaseModel):
    company: str
    job_title: str

class PitchResponse(BaseModel):
    content: str
    references: List[str] = []

class LogoRequest(BaseModel):
    style: str

class LeadCreateRequest(BaseModel):
    company_name: str
    contact_name: Optional[str] = None
    email: Optional[str] = None
    identified_need: Optional[str] = None
    source_job_url: Optional[str] = None

class LeadUpdateRequest(BaseModel):
    status: Optional[str] = None
    identified_need: Optional[str] = None
    pitch_content: Optional[str] = None

class PromoteLeadRequest(BaseModel):
    vendor_name: str
    email: Optional[str] = None
    notes: Optional[str] = None

class ApprovalRequest(BaseModel):
    notes: Optional[str] = None

class DraftBlogRequest(BaseModel):
    topic: str
    industry: Optional[List[str]] = None
    keywords: Optional[str] = None
