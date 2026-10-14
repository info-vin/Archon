"""
Data Models for Ollama Discovery Service (Phase 4.6.12 Hardening)

Defines dataclasses and TypedDict DTOs for discovered models, their capabilities, and instance health.
"""

from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict


class ModelParametersDTO(TypedDict, total=False):
    """DTO for model parameter metadata."""

    family: str
    parameter_size: str
    quantization: str
    format: str


class OllamaModelDetailsDTO(TypedDict, total=False):
    """DTO for detailed model information returned by /api/show."""

    family: str | None
    parameter_size: str | None
    quantization: str | None
    format: str | None
    parent_model: str | None
    parameters: ModelParametersDTO
    context_window: int | None
    max_context_length: int | None
    base_context_length: int | None
    custom_context_length: int | None
    architecture: str | None
    embedding_dimension: int | None
    parameter_count: int | str | None
    capabilities: list[str]
    block_count: int | None
    attention_heads: int | None
    file_type: int | str | None
    quantization_version: int | str | None
    basename: str | None
    size_label: str | None
    license: str | None
    finetune: str | None


class ModelDictDTO(TypedDict, total=False):
    """DTO for model dictionary representation in discovery results."""

    name: str
    instance_url: str
    size: int
    parameters: dict[str, Any] | ModelParametersDTO | None
    context_window: int | None
    max_context_length: int | None
    base_context_length: int | None
    custom_context_length: int | None
    architecture: str | None
    format: str | None
    parent_model: str | None
    capabilities: list[str]
    dimensions: NotRequired[int | None]


class HostStatusDTO(TypedDict, total=False):
    """DTO for host status in multi-instance discovery."""

    status: str
    models_count: str
    instance_url: str
    error: str


class DiscoveryResultDTO(TypedDict):
    """DTO for aggregated multi-instance model discovery result."""

    total_models: int
    chat_models: list[ModelDictDTO]
    embedding_models: list[ModelDictDTO]
    host_status: dict[str, HostStatusDTO]
    discovery_errors: list[str]
    unique_model_names: list[str]


@dataclass
class OllamaModel:
    """Represents a discovered Ollama model with comprehensive capabilities and metadata."""

    name: str
    tag: str
    size: int
    digest: str
    capabilities: list[str]  # 'chat', 'embedding', or both
    embedding_dimensions: int | None = None
    parameters: dict[str, Any] | None = None
    instance_url: str = ""
    last_updated: str | None = None

    # Comprehensive API data from /api/show endpoint
    context_window: int | None = None  # Current/active context length
    max_context_length: int | None = None  # Maximum supported context length
    base_context_length: int | None = None  # Original/base context length
    custom_context_length: int | None = None  # Custom num_ctx if set
    architecture: str | None = None
    block_count: int | None = None
    attention_heads: int | None = None
    format: str | None = None
    parent_model: str | None = None

    # Extended model metadata
    family: str | None = None
    parameter_size: str | None = None
    quantization: str | None = None
    parameter_count: int | None = None
    file_type: int | None = None
    quantization_version: int | None = None
    basename: str | None = None
    size_label: str | None = None
    license: str | None = None
    finetune: str | None = None
    embedding_dimension: int | None = None


@dataclass
class ModelCapabilities:
    """Model capability analysis results."""

    supports_chat: bool = False
    supports_embedding: bool = False
    supports_function_calling: bool = False
    supports_structured_output: bool = False
    embedding_dimensions: int | None = None
    parameter_count: str | None = None
    model_family: str | None = None
    quantization: str | None = None


@dataclass
class InstanceHealthStatus:
    """Health status for an Ollama instance."""

    is_healthy: bool
    response_time_ms: float | None = None
    models_available: int = 0
    error_message: str | None = None
    last_checked: str | None = None
