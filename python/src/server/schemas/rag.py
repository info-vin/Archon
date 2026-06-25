from typing import Any

from pydantic import BaseModel, Field


class RagSearchRequest(BaseModel):
    query: str = Field(..., description="The query string to search for")
    match_count: int = Field(default=10, description="Number of results to return")
    similarity_threshold: float = Field(
        default=0.82, description="Minimum similarity threshold for vector search (noise filtering)"
    )
    filter_dict: dict[str, Any] | None = Field(default_factory=dict, description="Metadata filter (JSONB)")
    source_filter: str | None = Field(default=None, description="Optional source ID filter")


class RagChunkResponse(BaseModel):
    id: int
    url: str
    chunk_number: int
    content: str
    metadata: dict[str, Any]
    source_id: str
    similarity: float
    match_type: str
    cdn_content: Any = None


class RagSearchResponse(BaseModel):
    status: str = "success"
    results: list[RagChunkResponse]
