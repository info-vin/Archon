
from typing import Literal

from pydantic import BaseModel, Field


class SearchCodeArgs(BaseModel):
    """Arguments for searching the codebase."""
    query: str = Field(
        ...,
        description="The code pattern or keyword to search for (e.g., 'get_supabase_client')."
    )
    source_id: str | None = Field(
        None,
        description="Optional source ID to filter search."
    )

class RagSearchArgs(BaseModel):
    """Arguments for searching the knowledge base."""
    query: str = Field(
        ...,
        description="Technical query (e.g., 'FastAPI middleware CORS')."
    )

class GenerateLogoArgs(BaseModel):
    """Arguments for generating an SVG logo."""
    prompt: str = Field(
        ...,
        description="Detailed description of the logo (e.g., 'A minimalist geometric ant')."
    )
    style: Literal["minimalist", "neon", "corporate", "geometric"] = Field(
        "minimalist",
        description="The visual style of the logo."
    )
