from pydantic import BaseModel, Field


class KnowledgeItemRequest(BaseModel):
    """Request model for updating a knowledge item."""

    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    knowledge_type: str | None = None
    is_active: bool | None = None


class CrawlRequest(BaseModel):
    """Request model for starting a crawl operation."""

    url: str
    max_depth: int = 2
    knowledge_type: str = "technical"
    tags: list[str] = Field(default_factory=list)
    max_concurrent: int = 3


class RagQueryRequest(BaseModel):
    """Request model for RAG queries."""

    query: str
    source_ids: list[str] | None = None
    limit: int = 5
    include_raw: bool = False


class CrawlStartResponse(BaseModel):
    """Response model for a started crawl operation."""

    success: bool
    progressId: str
    message: str
    estimatedDuration: str = "3-5 minutes"


class DocumentUploadResponse(BaseModel):
    """Response model for document upload endpoint."""

    status: str = Field(description="Upload status string, e.g., 'success'")
    progress_id: str = Field(description="Unique progress tracking ID for the upload task")
    message: str = Field(description="Informational message about the upload background process")
