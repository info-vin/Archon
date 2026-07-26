from typing import Any

from pydantic import BaseModel, Field


class ExtractionSchemaResponse(BaseModel):
    """Schema representing an extraction definition returned from the API."""
    id: str = Field(description="Unique identifier for the extraction schema")
    name: str = Field(description="Display name of the schema")
    domain_pattern: str | None = Field(default=None, description="Domain pattern this schema applies to")
    schema_definition: dict[str, Any] = Field(description="JSON Schema definition for extraction fields")
    target_role: str | None = Field(default=None, description="Target agent role for this schema")
    description: str | None = Field(default=None, description="Detailed description of the schema's purpose")
    created_at: str | None = Field(default=None, description="Creation timestamp")
    created_by: str | None = Field(default=None, description="User ID of the creator")


class SchemaCreateRequest(BaseModel):
    """Request payload for creating a new schema."""
    name: str = Field(description="Display name of the schema")
    domain_pattern: str | None = Field(default=None, description="Domain pattern this schema applies to")
    schema_definition: dict[str, Any] = Field(description="JSON Schema definition for extraction fields")
    target_role: str | None = Field(default=None, description="Target agent role for this schema")
    description: str | None = Field(default=None, description="Detailed description of the schema's purpose")


class SchemaUpdateRequest(BaseModel):
    """Request payload for updating an existing schema."""
    name: str | None = Field(default=None, description="Display name of the schema")
    domain_pattern: str | None = Field(default=None, description="Domain pattern this schema applies to")
    schema_definition: dict[str, Any] | None = Field(default=None, description="JSON Schema definition for extraction fields")
    target_role: str | None = Field(default=None, description="Target agent role for this schema")
    description: str | None = Field(default=None, description="Detailed description of the schema's purpose")


class AnalyzeUrlRequest(BaseModel):
    """Request payload for analyzing a URL."""
    url: str = Field(description="The URL to analyze for extraction fields")


class AnalyzeUrlResponse(BaseModel):
    """Response payload containing suggested schema fields from URL analysis."""
    fields: list[dict[str, Any]] | None = Field(default=None, description="List of suggested extraction fields")
    error: str | None = Field(default=None, description="Error message if analysis failed")


class RunExtractionRequest(BaseModel):
    """Request payload to trigger an extraction task."""
    url: str = Field(description="The URL to extract data from")
    schema_id: str = Field(description="The ID of the schema to use for extraction")


class RunExtractionResponse(BaseModel):
    """Response payload for an extraction task run."""
    success: bool = Field(description="Whether the extraction was successful")
    data: dict[str, Any] | None = Field(default=None, description="The extracted data payload")
    schema_used: str | None = Field(default=None, description="The name of the schema used")
    source_url: str | None = Field(default=None, description="The URL data was extracted from")
    error: str | None = Field(default=None, description="Error message if extraction failed")


class DeleteSchemaResponse(BaseModel):
    """Response payload for successful schema deletion."""
    success: bool = Field(description="Always true on successful deletion")
