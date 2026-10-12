from typing import Any

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


class CrawlActionResponse(BaseModel):
    """Response model for generic crawl actions (e.g., stop, refresh)."""

    success: bool
    message: str
    progressId: str | None = Field(default=None, description="Optional progress ID if an operation was initiated")


class DeleteSourceResponse(BaseModel):
    """Response model for deleting a knowledge source."""

    success: bool = Field(description="Whether the deletion operation succeeded")
    details: dict[str, Any] = Field(description="Details of deleted records and source information")


class AvailableSourceItem(BaseModel):
    """Item representation for available knowledge sources."""

    id: str = Field(description="Source ID")
    source_id: str = Field(description="Source ID")
    title: str = Field(description="Source title")
    knowledge_type: str = Field(default="technical", description="Knowledge type classification")
    url: str = Field(description="Source URL or reference")


class AvailableSourcesResponse(BaseModel):
    """Response model for available knowledge sources list."""

    sources: list[AvailableSourceItem] = Field(default_factory=list, description="List of available sources")
