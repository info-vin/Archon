"""
LLM Provider Service - Facade Layer
Modularized into src.server.services.llm/ for better maintainability.
Provides backward compatibility for existing imports and test patches.
"""

import asyncio
import uuid

import openai

from .credential_service import credential_service
from .llm.base import (
    MockChoice,
    MockLLMClient,
    MockMessage,
    MockResponse,
)
from .llm.clients import create_embedding_client, get_llm_client
from .llm.models import (
    get_embedding_model,
    get_supported_embedding_models,
    is_google_embedding_model,
    is_openai_embedding_model,
    is_reasoning_model,
    is_valid_embedding_model_for_provider,
    prepare_chat_completion_params,
    requires_max_completion_tokens,
)
from .llm.parsing import extract_json_from_reasoning, extract_message_text, synthesize_json_from_reasoning

# Import SHARED STATE from utils first to maintain PEP8 compliance while enabling mocks
from .llm.utils import (
    _cache_access_log,
    _settings_cache,
    get_cache_security_report,
    get_cached_settings,
    is_valid_provider,
    sanitize_for_log,
    set_cached_settings,
)
from .llm.validation import validate_provider_instance
from .token_usage_service import TokenUsageService

# PHYSICAL ALIASES for backward compatibility with legacy tests
_get_cached_settings = get_cached_settings
_set_cached_settings = set_cached_settings
_is_valid_provider = is_valid_provider
_sanitize_for_log = sanitize_for_log

# Export all symbols to maintain module-level visibility for tests and patches
__all__ = [
    "get_llm_client",
    "create_embedding_client",
    "MockLLMClient",
    "get_embedding_model",
    "is_openai_embedding_model",
    "is_google_embedding_model",
    "is_reasoning_model",
    "requires_max_completion_tokens",
    "prepare_chat_completion_params",
    "extract_message_text",
    "extract_json_from_reasoning",
    "synthesize_json_from_reasoning",
    "validate_provider_instance",
    "get_cache_security_report",
    "MockMessage",
    "MockChoice",
    "MockResponse",
    "_get_cached_settings",
    "_set_cached_settings",
    "_is_valid_provider",
    "_sanitize_for_log",
    "_settings_cache",
    "_cache_access_log",
    "openai",
    "credential_service",
    "TokenUsageService",
    "asyncio",
    "uuid",
    "is_valid_embedding_model_for_provider",
    "get_supported_embedding_models"
]
