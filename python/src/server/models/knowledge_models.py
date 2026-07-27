from typing import Any

from pydantic import BaseModel, Field


class SearchDocument(BaseModel):
    id: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)

class RerankRequest(BaseModel):
    query: str
    results: list[dict[str, Any]]
    content_key: str = "content"
    top_k: int = 5

class RerankResponse(BaseModel):
    success: bool
    results: list[dict[str, Any]] | None = None
    error: str | None = None
