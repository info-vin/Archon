from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from ..base_agent import ArchonDependencies


@dataclass
class DocumentDependencies(ArchonDependencies):
    """Dependencies for document operations."""
    project_id: str = ""  # Required but needs default value due to parent class having defaults
    current_document_id: str | None = None
    progress_callback: Any | None = None  # Callback for progress updates

class DocumentOperation(BaseModel):
    """Structured output for document operations."""
    operation_type: str = Field(description="Type of operation: create, update, delete, query")
    document_id: str | None = Field(description="ID of the document affected")
    document_type: str | None = Field(
        description="Type of document: prd, technical_spec, meeting_notes, etc."
    )
    title: str | None = Field(description="Document title")
    changes_made: list[str] = Field(description="List of specific changes made")
    success: bool = Field(description="Whether the operation was successful")
    message: str = Field(description="Human-readable message about the operation")
    content_preview: str | None = Field(
        description="Preview of the document content (first 200 chars)"
    )
