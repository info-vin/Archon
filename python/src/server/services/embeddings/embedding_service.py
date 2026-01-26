"""
Embedding Service

Handles all OpenAI embedding operations with proper rate limiting and error handling.
"""

import asyncio
import inspect
import os
from dataclasses import dataclass, field
from typing import Any

import httpx
import openai

from ...config.logfire_config import safe_span, search_logger
from ..credential_service import credential_service
from ..llm_provider_service import create_embedding_client, get_llm_client
from ..threading_service import get_threading_service
from .embedding_exceptions import (
    EmbeddingAPIError,
    EmbeddingError,
    EmbeddingQuotaExhaustedError,
    EmbeddingRateLimitError,
)


@dataclass
class EmbeddingBatchResult:
    """Result of batch embedding creation with success/failure tracking."""

    embeddings: list[list[float]] = field(default_factory=list)
    failed_items: list[dict[str, Any]] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    texts_processed: list[str] = field(default_factory=list)  # Successfully processed texts

    def add_success(self, embedding: list[float], text: str):
        """Add a successful embedding."""
        self.embeddings.append(embedding)
        self.texts_processed.append(text)
        self.success_count += 1

    def add_failure(self, text: str, error: Exception, batch_index: int | None = None):
        """Add a failed item with error details."""
        error_dict = {
            "text": text[:200] if text else None,
            "error": str(error),
            "error_type": type(error).__name__,
            "batch_index": batch_index,
        }

        # Add extra context from EmbeddingError if available
        if isinstance(error, EmbeddingError):
            error_dict.update(error.to_dict())

        self.failed_items.append(error_dict)
        self.failure_count += 1

    @property
    def has_failures(self) -> bool:
        return self.failure_count > 0

    @property
    def total_requested(self) -> int:
        return self.success_count + self.failure_count


# Provider-aware client factory
get_openai_client = get_llm_client


async def create_embedding(text: str) -> list[float]:
    """
    Create an embedding for a single text using the configured provider with failover.

    Args:
        text: Text to create an embedding for

    Returns:
        List of floats representing the embedding

    Raises:
        EmbeddingQuotaExhaustedError: When OpenAI quota is exhausted
        EmbeddingRateLimitError: When rate limited
        EmbeddingAPIError: For other API errors
    """
    try:
        result = await create_embeddings_batch([text])
        if not result.embeddings:
            # Check if there were failures
            if result.has_failures and result.failed_items:
                # Re-raise the original error for single embeddings
                error_info = result.failed_items[0]
                error_msg = error_info.get("error", "Unknown error")
                if "quota" in error_msg.lower():
                    raise EmbeddingQuotaExhaustedError(
                        f"OpenAI quota exhausted: {error_msg}", text_preview=text
                    )
                elif "rate" in error_msg.lower():
                    raise EmbeddingRateLimitError(f"Rate limit hit: {error_msg}", text_preview=text)
                else:
                    raise EmbeddingAPIError(
                        f"Failed to create embedding: {error_msg}", text_preview=text
                    )
            else:
                raise EmbeddingAPIError(
                    "No embeddings returned from batch creation", text_preview=text
                )
        return result.embeddings[0]
    except EmbeddingError:
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        # Convert to appropriate exception type
        error_msg = str(e)
        search_logger.error(f"Embedding creation failed: {error_msg}", exc_info=True)
        search_logger.error(f"Failed text preview: {text[:100]}...")

        if "insufficient_quota" in error_msg:
            raise EmbeddingQuotaExhaustedError(
                f"OpenAI quota exhausted: {error_msg}", text_preview=text
            ) from e
        elif "rate_limit" in error_msg.lower():
            raise EmbeddingRateLimitError(f"Rate limit hit: {error_msg}", text_preview=text) from e
        else:
            raise EmbeddingAPIError(
                f"Embedding error: {error_msg}", text_preview=text, original_error=e
            ) from e


async def create_embeddings_batch(
    texts: list[str],
    progress_callback: Any | None = None,
) -> EmbeddingBatchResult:
    """
    Create embeddings for multiple texts with graceful failure handling and provider failover.

    This function attempts to use the primary embedding provider, and on failure,
    transparently switches to a configured fallback provider.

    Args:
        texts: List of texts to create embeddings for
        progress_callback: Optional callback for progress reporting

    Returns:
        EmbeddingBatchResult with successful embeddings and failure details
    """
    if not texts:
        return EmbeddingBatchResult()

    # Validate that all items in texts are strings
    validated_texts = []
    for i, text in enumerate(texts):
        if not isinstance(text, str):
            search_logger.error(f"Invalid text type at index {i}: {type(text)}, value: {text}", exc_info=True)
            try:
                validated_texts.append(str(text))
            except Exception as e:
                search_logger.error(f"Failed to convert text at index {i} to string: {e}", exc_info=True)
                validated_texts.append("")
        else:
            validated_texts.append(text)
    texts = validated_texts

    result = EmbeddingBatchResult()
    threading_service = get_threading_service() # Variable assigned and used now

    with safe_span("create_embeddings_batch", text_count=len(texts), total_chars=sum(len(t) for t in texts)) as span:
        try:
            configs = await credential_service.get_embedding_provider_configs()
            if not configs:
                raise ValueError("No valid embedding providers configured.")

            last_exception = None
            for idx, config in enumerate(configs):
                client: openai.AsyncOpenAI | None = None
                provider_name = config.get("provider", "unknown")
                is_last_provider = (idx == len(configs) - 1)

                try:
                    search_logger.info(f"Attempting embedding creation with provider: {provider_name}")
                    client = await create_embedding_client(config)

                    rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
                    batch_size = int(rag_settings.get("EMBEDDING_BATCH_SIZE", "100"))
                    embedding_dimensions = int(rag_settings.get("EMBEDDING_DIMENSIONS", "1536"))

                    all_batches_succeeded_for_provider = True
                    for i in range(0, len(texts), batch_size):
                        batch = texts[i : i + batch_size]
                        batch_index = i // batch_size # Variable used now

                        try:
                            batch_tokens = sum(len(text.split()) for text in batch) * 1.3
                            rate_limit_callback = None
                            if progress_callback:
                                async def rate_limit_callback(data: dict, res=result):
                                    processed = res.success_count + res.failure_count
                                    message = f"Rate limited: {data.get('message', 'Waiting...')}"
                                    await progress_callback(message, (processed / len(texts)) * 100)

                            async with threading_service.rate_limited_operation(batch_tokens, rate_limit_callback): # Re-introduced rate limiting
                                retry_count = 0
                                max_retries = 3
                                while retry_count < max_retries:
                                    try:
                                        embedding_model = config.get("embedding_model")

                                        if provider_name == "google":
                                            # Native Google API call (using proven v1beta + header variant)
                                            async with httpx.AsyncClient(timeout=20.0) as http_client:
                                                # Use gemini-embedding-001 which is proven stable
                                                # Fallback to config model if not explicit, then to a stable default
                                                stable_model = config.get("embedding_model") or "gemini-embedding-001"
                                                api_key_to_use = (config.get("api_key") or os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")

                                                url = f"https://generativelanguage.googleapis.com/v1beta/models/{stable_model}:embedContent"
                                                headers = {"x-goog-api-key": api_key_to_use}

                                                for text_item in batch:
                                                    payload = {
                                                        "content": {"parts": [{"text": text_item}]},
                                                        "outputDimensionality": 768
                                                    }
                                                    resp = await http_client.post(url, headers=headers, json=payload)

                                                    if resp.status_code == 200:
                                                        data = resp.json()
                                                        result.add_success(data["embedding"]["values"], text_item)
                                                    else:
                                                        search_logger.error(f"Google native API failed: Status {resp.status_code}, Body: {resp.text}")
                                                        raise EmbeddingAPIError(f"Google error {resp.status_code}: {resp.text}")
                                        else:
                                            # Standard OpenAI-compatible call
                                            api_params = {
                                                "model": embedding_model,
                                                "input": batch,
                                            }
                                            # OpenAI-specific: only add dimensions for compatible models
                                            if provider_name != "google":
                                                api_params["dimensions"] = embedding_dimensions

                                            response = await client.embeddings.create(**api_params)
                                            for item, text_item in zip(response.data, batch, strict=False):
                                                result.add_success(item.embedding, text_item)
                                        break
                                    except openai.RateLimitError as e:
                                        error_message = str(e)
                                        if "insufficient_quota" in error_message:
                                            search_logger.error(f"Provider {provider_name} has insufficient quota.", exc_info=True)
                                            raise

                                        retry_count += 1
                                        if retry_count >= max_retries:
                                            search_logger.error(f"Rate limit retries exceeded for provider {provider_name}. Batch {batch_index}.", exc_info=True)
                                            raise

                                        wait_time = 2 ** retry_count
                                        search_logger.warning(f"Rate limit hit for {provider_name}. Batch {batch_index}. Waiting {wait_time}s before retry {retry_count}/{max_retries}")
                                        await asyncio.sleep(wait_time)
                        except Exception as e:
                            # Re-raise specific exceptions that should trigger provider failover
                            if isinstance(e, openai.AuthenticationError | openai.PermissionDeniedError | openai.APIConnectionError | openai.RateLimitError):
                                raise

                            all_batches_succeeded_for_provider = False
                            search_logger.error(f"Batch {batch_index} failed for provider {provider_name}: {e}", exc_info=True) # batch_index used
                            for text in batch:
                                result.add_failure(text, EmbeddingAPIError(f"Batch {batch_index} failed: {e}", original_error=e), batch_index)

                        if progress_callback:
                            processed = result.success_count + result.failure_count
                            progress = (processed / len(texts)) * 100
                            message = f"Processed {processed}/{len(texts)} texts"
                            if result.has_failures:
                                message += f" ({result.failure_count} failed)"
                            await progress_callback(message, progress)
                        await asyncio.sleep(0.01)

                    if all_batches_succeeded_for_provider:
                        span.set_attribute("provider_used", provider_name)
                        return result

                except (openai.AuthenticationError, openai.PermissionDeniedError, openai.APIConnectionError, openai.RateLimitError, ValueError) as e:
                    last_exception = e
                    search_logger.warning(f"Provider '{provider_name}' failed. Last batch failed with error: {e}. Trying next provider if available.")
                    if is_last_provider:
                        search_logger.error(f"All embedding providers failed. Last error from '{provider_name}': {e}", exc_info=True)
                        raise
                finally:
                    if client:
                        # Safe close that handles both real AsyncOpenAI clients and MagicMocks
                        try:
                            # Try standard close method
                            close_method = getattr(client, "close", None)
                            if callable(close_method):
                                is_coroutine = inspect.iscoroutinefunction(close_method) or inspect.isawaitable(close_method)
                                if is_coroutine:
                                    await close_method()
                                else:
                                    close_method()
                            # Fallback for older clients or mocks
                            elif hasattr(client, "aclose"):
                                await client.aclose()
                        except Exception as cleanup_err:
                            search_logger.warning(f"Error closing client: {cleanup_err}")

            raise last_exception or ValueError("All providers failed without a specific exception.")

        except Exception as e:
            span.set_attribute("catastrophic_failure", True)
            search_logger.error(f"Catastrophic failure in batch embedding: {e}", exc_info=True)
            processed_count = result.success_count + result.failure_count
            if processed_count < len(texts):
                final_error = EmbeddingAPIError(f"Catastrophic failure: {str(e)}", original_error=e)
                for text in texts[processed_count:]:
                    result.add_failure(text, final_error)
            return result


# Deprecated functions - kept for backward compatibility
async def get_openai_api_key() -> str | None:
    """
    DEPRECATED: Use os.getenv("OPENAI_API_KEY") directly.
    API key is loaded into environment at startup.
    """
    return os.getenv("OPENAI_API_KEY")
