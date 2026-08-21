from typing import Any

from pydantic import BaseModel, Field


class KnowledgeItemsResponse(BaseModel):
    items: list[dict[str, Any]] = Field(description="List of knowledge items")
    total: int = Field(description="Total number of items available")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Number of items per page")

class DatabaseMetricsResponse(BaseModel):
    sources_count: int = Field(description="Number of sources")
    pages_count: int = Field(description="Number of crawled pages")
    code_examples_count: int = Field(description="Number of code examples")
    timestamp: str = Field(description="Timestamp of the metrics snapshot")
    average_pages_per_source: float = Field(description="Average pages per source")
