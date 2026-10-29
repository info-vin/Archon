from typing import Any

from pydantic import BaseModel, ConfigDict, Field


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
    source: str | None = None
    limit: int = 5
    match_count: int | None = None
    include_raw: bool = False
    return_mode: str | None = None

    model_config = ConfigDict(extra="allow")


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


class KnowledgeItemResponse(BaseModel):
    """Response model for a single knowledge item."""

    source_id: str = Field(description="Unique source identifier")
    title: str = Field(default="", description="Source title")
    summary: str | None = Field(default=None, description="Summary description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata key-value pairs")
    source_url: str | None = Field(default=None, description="Source URL")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    updated_at: str | None = Field(default=None, description="Last update timestamp")

    model_config = {"extra": "allow"}


class KnowledgeItemListResponse(BaseModel):
    """Response model for a list of knowledge items with pagination."""

    items: list[KnowledgeItemResponse] = Field(default_factory=list, description="List of knowledge items")
    total: int = Field(default=0, description="Total count of knowledge items")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=50, description="Number of items per page")


class ChunkPagination(BaseModel):
    """Pagination details for document chunks."""

    total: int = Field(default=0, description="Total number of chunks")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=50, description="Items per page")
    total_pages: int = Field(default=0, description="Total number of pages")


class ChunkItem(BaseModel):
    """Document chunk item representation."""

    id: str | int = Field(description="Chunk ID")
    source_id: str = Field(description="Source identifier")
    content: str | None = Field(default=None, description="Text chunk content")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Chunk metadata")
    url: str | None = Field(default=None, description="Chunk page URL")

    model_config = {"extra": "allow"}


class SourceChunksResponse(BaseModel):
    """Response model for document chunks list."""

    chunks: list[ChunkItem] = Field(default_factory=list, description="List of document chunks")
    pagination: ChunkPagination = Field(
        default_factory=ChunkPagination, description="Pagination details for document chunks"
    )


class KnowledgeSearchItemResponse(BaseModel):
    """Response model for knowledge search results."""

    id: int | str | None = Field(default=None, description="Chunk or record ID")
    url: str | None = Field(default=None, description="Page or source URL")
    chunk_number: int | None = Field(default=None, description="Chunk index within source document")
    content: str | None = Field(default="", description="Text content chunk")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata key-value pairs")
    source_id: str | None = Field(default=None, description="Unique source identifier")
    similarity: float | None = Field(default=0.0, description="Vector similarity score")

    model_config = ConfigDict(extra="allow")


class RagQueryResultItem(BaseModel):
    """Individual search result item within a RAG query response."""

    id: str | int = Field(description="Result item ID")
    content: str = Field(description="Result content or excerpt")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary")
    similarity_score: float = Field(default=0.0, description="Similarity or boosted relevance score")

    model_config = ConfigDict(extra="allow")


class RagQueryResponse(BaseModel):
    """Response model for full RAG query endpoint (/api/rag/query)."""

    success: bool = Field(default=True, description="Query execution status")
    results: list[RagQueryResultItem] = Field(default_factory=list, description="List of search result items")
    query: str = Field(description="Original search query")
    source: str | None = Field(default=None, description="Filtered source domain if specified")
    match_count: int = Field(default=5, description="Requested max match count")
    total_found: int = Field(default=0, description="Total results returned")
    execution_path: str = Field(default="rag_service_pipeline", description="Pipeline execution identifier")
    search_mode: str = Field(default="vector", description="Search strategy used (e.g. vector, hybrid)")
    reranking_applied: bool = Field(default=False, description="Whether reranking was executed")

    model_config = ConfigDict(extra="allow")
