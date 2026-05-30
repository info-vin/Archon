"""
Batch processing logic for embedding services.
"""

import asyncio
import inspect
import os
from typing import Any, cast

import httpx
import openai

from ...config.logfire_config import safe_span, search_logger
from ..credential_service import credential_service
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
    if os.getenv("OFFLINE_MODE", "false").lower() == "true":
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
            configs = await credential_service.get_embedding_provider_configs()
            if not configs:
                raise ValueError("No valid embedding providers configured.")

            last_exception = None
            for idx, config in enumerate(configs):
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
                                max_retries = 3
                                while retry_count < max_retries:
                                    try:
                                        embedding_model = config.get("embedding_model")

                                        if provider_name == "google":
                                            # Native Google API call (using proven v1beta + header variant)
                                            async with httpx.AsyncClient(timeout=20.0) as http_client:
                                                # Use gemini-embedding-001 which is proven stable
                                                # Fallback to config model if not explicit, then to a stable default
                                                stable_model = config.get("embedding_model")
                                                if not stable_model:
                                                    raise ValueError(
                                                        "embedding_model is not configured in provider settings"
                                                    )
                                                api_key_to_use = (
                                                    (config.get("api_key") or os.getenv("GEMINI_API_KEY") or "")
                                                    .strip()
                                                    .strip('"')
                                                    .strip("'")
                                                )

                                                url = f"https://generativelanguage.googleapis.com/v1beta/models/{stable_model}:embedContent"
                                                headers = {"x-goog-api-key": api_key_to_use}

                                                for text_item in batch:
                                                    payload = {
                                                        "content": {"parts": [{"text": text_item}]},
                                                        "outputDimensionality": 768,
                                                    }
                                                    resp = await http_client.post(url, headers=headers, json=payload)

                                                    if resp.status_code == 200:
                                                        data = resp.json()
                                                        result.add_success(data["embedding"]["values"], text_item)
                                                    else:
                                                        search_logger.error(
                                                            f"Google native API failed: Status {resp.status_code}, Body: {resp.text}"
                                                        )
                                                        raise EmbeddingAPIError(
                                                            f"Google error {resp.status_code}: {resp.text}"
                                                        )
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
                                                result.add_success(item.embedding, text_item)
                                        break
                                    except openai.RateLimitError as e:
                                        error_message = str(e)
                                        if "insufficient_quota" in error_message:
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

                                        wait_time = 2**retry_count
                                        search_logger.warning(
                                            f"Rate limit hit for {provider_name}. Batch {batch_index}. Waiting {wait_time}s before retry {retry_count}/{max_retries}"
                                        )
                                        await asyncio.sleep(wait_time)
                        except Exception as e:
                            # Re-raise specific exceptions that should trigger provider failover
                            if isinstance(
                                e,
                                openai.AuthenticationError
                                | openai.PermissionDeniedError
                                | openai.APIConnectionError
                                | openai.RateLimitError,
                            ):
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
