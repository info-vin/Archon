
from typing import Any

from pydantic import BaseModel, Field


class InstanceValidationRequest(BaseModel):
    instance_url: str = Field(..., description="URL of the Ollama instance")
    instance_type: str | None = Field(None, description="Instance type: chat, embedding, or both")
    timeout_seconds: int | None = Field(30, description="Timeout for validation in seconds")


class InstanceValidationResponse(BaseModel):
    is_valid: bool
    instance_url: str
    response_time_ms: float | None
    models_available: int
    error_message: str | None
    capabilities: dict[str, Any]
    health_status: dict[str, Any]


class ModelDiscoveryRequest(BaseModel):
    instance_urls: list[str] = Field(..., description="List of Ollama instance URLs")
    include_capabilities: bool = Field(True, description="Include model capability detection")
    cache_ttl: int | None = Field(300, description="Cache TTL in seconds")


class ModelDiscoveryResponse(BaseModel):
    total_models: int
    chat_models: list[dict[str, Any]]
    embedding_models: list[dict[str, Any]]
    host_status: dict[str, dict[str, Any]]
    discovery_errors: list[str]
    unique_model_names: list[str]


class EmbeddingRouteRequest(BaseModel):
    model_name: str = Field(..., description="Name of the embedding model")
    instance_url: str = Field(..., description="URL of the Ollama instance")
    text_sample: str | None = Field(None, description="Optional text sample for optimization")


class EmbeddingRouteResponse(BaseModel):
    target_column: str
    model_name: str
    instance_url: str
    dimensions: int
    confidence: float
    fallback_applied: bool
    routing_strategy: str
    performance_score: float | None


class ModelDiscoveryAndStoreRequest(BaseModel):
    instance_urls: list[str] = Field(..., description="List of Ollama instance URLs")
    force_refresh: bool = Field(False, description="Force refresh")


class StoredModelInfo(BaseModel):
    name: str
    host: str
    model_type: str
    size_mb: int | None = None
    context_length: int | None = None
    parameters: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    archon_compatibility: str
    compatibility_features: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    performance_rating: str | None = None
    description: str | None = None
    last_updated: str
    embedding_dimensions: int | None = None


class ModelListResponse(BaseModel):
    models: list[StoredModelInfo]
    total_count: int
    instances_checked: int
    last_discovery: str | None = None
    cache_status: str


class ModelCapabilityTestRequest(BaseModel):
    model_name: str
    instance_url: str
    test_function_calling: bool = True
    test_structured_output: bool = True
    timeout_seconds: int = 15


class ModelCapabilityTestResponse(BaseModel):
    model_name: str
    instance_url: str
    test_results: dict[str, Any]
    compatibility_assessment: dict[str, Any]
    test_duration_seconds: float
    errors: list[str] = Field(default_factory=list)


class InstanceHealthSummary(BaseModel):
    total_instances: int
    healthy_instances: int
    unhealthy_instances: int
    average_response_time_ms: float | None = None

class InstanceHealthDetail(BaseModel):
    is_healthy: bool
    response_time_ms: float | None = None
    models_available: int | None = None
    error_message: str | None = None
    last_checked: str | None = None

class InstanceHealthResponse(BaseModel):
    summary: InstanceHealthSummary
    instance_status: dict[str, InstanceHealthDetail]
    timestamp: str
