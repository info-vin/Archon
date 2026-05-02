"""
Embedding Service

Handles single embedding operations and serves as the facade for batch processing.
"""

from ...config.logfire_config import search_logger
from ..llm_provider_service import get_llm_client
from .batch_processor import create_embeddings_batch
from .embedding_exceptions import (
    EmbeddingAPIError,
    EmbeddingError,
    EmbeddingQuotaExhaustedError,
    EmbeddingRateLimitError,
)

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
                    raise EmbeddingQuotaExhaustedError(f"OpenAI quota exhausted: {error_msg}", text_preview=text)
                elif "rate" in error_msg.lower():
                    raise EmbeddingRateLimitError(f"Rate limit hit: {error_msg}", text_preview=text)
                else:
                    raise EmbeddingAPIError(f"Failed to create embedding: {error_msg}", text_preview=text)
            else:
                raise EmbeddingAPIError("No embeddings returned from batch creation", text_preview=text)
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
            raise EmbeddingQuotaExhaustedError(f"OpenAI quota exhausted: {error_msg}", text_preview=text) from e
        elif "rate_limit" in error_msg.lower():
            raise EmbeddingRateLimitError(f"Rate limit hit: {error_msg}", text_preview=text) from e
        else:
            raise EmbeddingAPIError(f"Embedding error: {error_msg}", text_preview=text, original_error=e) from e
