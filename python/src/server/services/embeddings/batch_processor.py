"""
Batch processing logic for embedding services.
"""

import asyncio
import inspect
from typing import Any, cast

import httpx
import openai

from ...config.logfire_config import safe_span, search_logger
from ..credential_service import credential_service
from ..credentials.provider_configs import get_embedding_provider_configs
from ..llm_provider_service import create_embedding_client
from ..threading_service import get_threading_service
from .embedding_exceptions import (
    EmbeddingAPIError,
)
from .models import EmbeddingBatchResult


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

    # Dynamic offline mode handling using sentence-transformers
    from ...config.config import get_config
    if get_config().offline_mode:
        search_logger.info("OFFLINE_MODE is enabled. Generating embeddings locally using 'all-MiniLM-L6-v2'.")
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")

            # SentenceTransformer encode executes synchronously, wrap in executor to keep it async friendly
            loop = asyncio.get_event_loop()
            embeddings_np = await loop.run_in_executor(
                None, lambda: model.encode(texts, show_progress_bar=False)
            )

            result = EmbeddingBatchResult()
            for text_item, emb in zip(texts, embeddings_np, strict=False):
                result.add_success(emb.tolist(), text_item)
            return result
        except Exception as e:
            search_logger.error(f"Failed to generate local embeddings: {e}", exc_info=True)
            result = EmbeddingBatchResult()
            final_error = EmbeddingAPIError(f"Local embedding failure: {str(e)}", original_error=e)
            for text_item in texts:
                result.add_failure(text_item, final_error)
            return result

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
    threading_service = get_threading_service()

    with safe_span("create_embeddings_batch", text_count=len(texts), total_chars=sum(len(t) for t in texts)) as span:
        try:
            configs = await get_embedding_provider_configs(credential_service)
            if not configs:
                raise ValueError("No valid embedding providers configured.")

            last_exception = None
            for idx, config in enumerate(configs):
                result = EmbeddingBatchResult()
                client: openai.AsyncOpenAI | None = None
                provider_name = config.get("provider", "unknown")
                is_last_provider = idx == len(configs) - 1

                try:
                    search_logger.info(f"Attempting embedding creation with provider: {provider_name}")
                    client = await create_embedding_client(config)

                    rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
                    batch_size = int(rag_settings.get("EMBEDDING_BATCH_SIZE", "100"))
                    embedding_dimensions = int(rag_settings.get("EMBEDDING_DIMENSIONS", "768"))

                    all_batches_succeeded_for_provider = True
                    for i in range(0, len(texts), batch_size):
                        batch = texts[i : i + batch_size]
                        batch_index = i // batch_size

                        try:
                            # PERFORMANCE: Replaced sum(len(text.split())...) with a faster loop and .count(' ')
                            # which avoids allocating lists for every text chunk.
                            batch_tokens_raw = 0
                            for text in batch:
                                batch_tokens_raw += text.count(" ") + 1
                            batch_tokens = int(batch_tokens_raw * 1.3)
                            rate_limit_callback = None
                            if progress_callback:

                                async def rate_limit_callback(data: dict, res=result):
                                    processed = res.success_count + res.failure_count
                                    message = f"Rate limited: {data.get('message', 'Waiting...')}"
                                    await progress_callback(message, (processed / len(texts)) * 100)

                            async with threading_service.rate_limited_operation(
                                batch_tokens, rate_limit_callback
                            ):  # Re-introduced rate limiting
                                retry_count = 0
                                max_retries = 6
                                while retry_count < max_retries:
                                    try:
                                        embedding_model = config.get("embedding_model")

                                        if provider_name == "google":
                                            from google import genai
                                            from google.genai import types

                                            stable_model = config.get("embedding_model")
                                            if not stable_model:
                                                raise ValueError(
                                                    "embedding_model is not configured in provider settings"
                                                )
                                            from ...config.config import get_config
                                            api_key_to_use = (
                                                (config.get("api_key") or get_config().gemini_api_key or "")
                                                .strip()
                                                .strip('"')
                                                .strip("'")
                                            )

                                            client_g = genai.Client(api_key=api_key_to_use)

                                            # outputDimensionality is not supported for older embedding-001 model
                                            if "embedding-001" not in stable_model.lower():
                                                embed_config = types.EmbedContentConfig(output_dimensionality=embedding_dimensions)
                                            else:
                                                embed_config = None

                                            resp = await client_g.aio.models.embed_content(
                                                model=stable_model,
                                                contents=cast(Any, batch),
                                                config=embed_config
                                            )

                                            if not resp.embeddings or len(resp.embeddings) != len(batch):
                                                raise EmbeddingAPIError("Google API returned unexpected number of embeddings")

                                            for emb, text_item in zip(resp.embeddings, batch, strict=False):
                                                if emb.values is not None:
                                                    emb_vals = emb.values
                                                    if len(emb_vals) > embedding_dimensions:
                                                        emb_vals = emb_vals[:embedding_dimensions]
                                                    result.add_success(emb_vals, text_item)
                                        else:
                                            # Standard OpenAI-compatible call
                                            if provider_name != "google":
                                                response = await client.embeddings.create(
                                                    model=cast(str, embedding_model),
                                                    input=batch,
                                                    dimensions=embedding_dimensions,
                                                )
                                            else:
                                                response = await client.embeddings.create(
                                                    model=cast(str, embedding_model), input=batch
                                                )

                                            for item, text_item in zip(response.data, batch, strict=False):
                                                emb_vals = item.embedding
                                                if len(emb_vals) > embedding_dimensions:
                                                    emb_vals = emb_vals[:embedding_dimensions]
                                                result.add_success(emb_vals, text_item)
                                        break
                                    except Exception as e:
                                        error_message = str(e).lower()
                                        
                                        # Detect 429 / Rate Limit
                                        is_rate_limit = (
                                            isinstance(e, openai.RateLimitError) 
                                            or "429" in error_message 
                                            or "rate limit" in error_message 
                                            or "resource_exhausted" in error_message
                                            or "quota" in error_message
                                        )
                                        
                                        if not is_rate_limit:
                                            raise
                                            
                                        # Only hard-fail on OpenAI's specific out-of-money error. 
                                        # Google GenAI uses 'quota' for standard RPM rate limits, so we MUST retry them!
                                        if "insufficient_quota" in error_message and "openai" in str(type(e)).lower():
                                            search_logger.error(
                                                f"Provider {provider_name} has insufficient quota.", exc_info=True
                                            )
                                            raise

                                        retry_count += 1
                                        if retry_count >= max_retries:
                                            search_logger.error(
                                                f"Rate limit retries exceeded for provider {provider_name}. Batch {batch_index}.",
                                                exc_info=True,
                                            )
                                            raise

                                        wait_time = min(2**retry_count, 30)
                                        search_logger.warning(
                                            f"Rate limit hit for {provider_name}. Batch {batch_index}. Waiting {wait_time}s before retry {retry_count}/{max_retries}"
                                        )
                                        await asyncio.sleep(wait_time)
                        except Exception as e:
                            # Re-raise specific exceptions that should trigger provider failover
                            err_msg = str(e).lower()
                            is_rate_limit_outer = (
                                isinstance(e, openai.RateLimitError) 
                                or "429" in err_msg 
                                or "rate limit" in err_msg
                                or "resource_exhausted" in err_msg
                                or "quota" in err_msg
                            )
                            
                            if isinstance(
                                e,
                                (openai.AuthenticationError, openai.PermissionDeniedError, openai.APIConnectionError, httpx.RequestError)
                            ) or is_rate_limit_outer:
                                raise

                            all_batches_succeeded_for_provider = False
                            search_logger.error(
                                f"Batch {batch_index} failed for provider {provider_name}: {e}", exc_info=True
                            )
                            for text in batch:
                                result.add_failure(
                                    text,
                                    EmbeddingAPIError(f"Batch {batch_index} failed: {e}", original_error=e),
                                    batch_index,
                                )

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
                    else:
                        raise EmbeddingAPIError(f"Provider {provider_name} failed on one or more batches.")

                except Exception as e:
                    last_exception = e
                    search_logger.warning(
                        f"Provider '{provider_name}' failed with {type(e).__name__}: {e}. Trying next if available."
                    )
                    if is_last_provider:
                        search_logger.error(
                            f"All embedding providers failed. Final source of failure '{provider_name}': {e}",
                            exc_info=True,
                        )
                        raise e
                finally:
                    if client:
                        # Safe close that handles both real AsyncOpenAI clients and MagicMocks
                        try:
                            # Try standard close method
                            close_method = getattr(client, "close", None)
                            if callable(close_method):
                                is_coroutine = inspect.iscoroutinefunction(close_method) or inspect.isawaitable(
                                    close_method
                                )
                                if is_coroutine:
                                    await close_method()
                                else:
                                    close_method()
                            # Fallback for older clients or mocks
                            elif hasattr(client, "aclose"):
                                await client.aclose()
                        except Exception as cleanup_err:
                            search_logger.warning(f"Error closing client: {cleanup_err}")

            if last_exception:
                raise last_exception

            raise ValueError("No embedding providers were attempted. Please verify API Key configurations in Settings.")

        except Exception as e:
            span.set_attribute("catastrophic_failure", True)
            search_logger.error(f"Catastrophic failure in batch embedding: {e}", exc_info=True)
            processed_count = result.success_count + result.failure_count
            if processed_count < len(texts):
                final_error = EmbeddingAPIError(f"Catastrophic failure: {str(e)}", original_error=e)
                for text in texts[processed_count:]:
                    result.add_failure(text, final_error)
            return result
