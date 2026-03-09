"""
Data Models for Ollama Discovery Service (Phase 4.6.12 Hardening)

Defines dataclasses for discovered models, their capabilities, and instance health.
"""

from dataclasses import dataclass
from typing import Any, Optional


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
