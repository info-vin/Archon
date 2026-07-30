"""
Contextual Embedding Service

Handles generation of contextual embeddings for improved RAG retrieval.
Includes proper rate limiting for OpenAI API calls.
"""

import asyncio
from typing import cast

import openai

from ...config.logfire_config import search_logger
from ..llm_provider_service import get_llm_client
from ..threading_service import get_threading_service


async def generate_contextual_embedding(
    full_document: str, chunk: str, provider: str | None = None
) -> tuple[str, bool]:
    """
    Generate contextual information for a chunk with proper rate limiting.
    Uses Gemini 2.5 Flash (preferred) or default chat model.
    """
    threading_service = get_threading_service()

    # Gemini 2.5 Flash has 1M+ context, we can comfortably use 20k chars (~5k tokens)
    doc_context = full_document[:20000] if len(full_document) > 20000 else full_document
    estimated_tokens = len(doc_context.split()) + len(chunk.split()) + 200

    try:
        async with threading_service.rate_limited_operation(estimated_tokens):
            async with get_llm_client(provider=provider) as client:
                # Optimized prompt following Anthropic's "Situating" pattern
                prompt = f"""<document>
{doc_context}
</document>
Here is the chunk we want to situate within the whole document:
<chunk>
{chunk}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk.
Answer only with the succinct context and nothing else. Do not repeat the chunk content."""

                model = await _get_model_choice(provider)

                # Force Gemini 2.5 Flash if available as it's the project standard for fast/cheap reasoning
                if "gemini" in model.lower() and "flash" not in model.lower():
                    from ...config.model_ssot import SYSTEM_MODELS

                    model = SYSTEM_MODELS["DEFAULT_TEXT"]

                from ..prompt_service import prompt_service
                default_system_prompt = "You are a professional librarian that provides high-signal contextual metadata for RAG retrieval."
                system_prompt = prompt_service.get_prompt("EMBED_CONTEXT_GENERATOR", default_system_prompt)

                response = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,  # Low temperature for consistency
                    max_tokens=300,
                )

                context = response.choices[0].message.content.strip()
                # Prepend context as per Anthropic strategy
                contextual_text = f"{context}\n\n{chunk}"

                return contextual_text, True

    except openai.RateLimitError:
        # Physical In-place Retry: Wait for quota recovery
        from ...schemas.settings import SystemTaskConfig
        from ...services.settings_service import SettingsService
        try:
            raw_settings = SettingsService().get_all_settings()
            config = SystemTaskConfig.model_validate(raw_settings)
            delay = config.embedding_process_delay_secs
        except Exception:
            delay = 15
        search_logger.warning(f"429 Quota Exhausted. Waiting {delay}s for recovery...")
        await asyncio.sleep(delay)
        try:
            # Recursive retry once
            return await generate_contextual_embedding(full_document, chunk, provider=provider)
        except Exception as retry_err:
            search_logger.error(f"Retry failed after 429: {retry_err}")
            return chunk, False

    except Exception as e:
        search_logger.error(f"Error generating contextual embedding: {e}")
        return chunk, False


async def process_chunk_with_context(url: str, content: str, full_document: str) -> tuple[str, bool]:
    """
    Process a single chunk with contextual embedding using async/await.

    Args:
        url: URL of the document
        content: The chunk content
        full_document: The complete document text

    Returns:
        Tuple containing:
        - The contextual text that situates the chunk within the document
        - Boolean indicating if contextual embedding was performed
    """
    return await generate_contextual_embedding(full_document, content)


async def _get_model_choice(provider: str | None = None) -> str:
    """Get model choice from credential service."""
    from ..credential_service import credential_service
    from ..credentials.provider_configs import get_active_provider

    # Get the active provider configuration
    provider_config = await get_active_provider(credential_service, "llm")
    model = provider_config.get("chat_model")
    if not model:
        raise ValueError("chat_model is not configured in provider_config")
    model = cast(str, model)

    search_logger.debug(f"Using model from credential service: {model}")

    return model


async def generate_contextual_embeddings_batch(
    full_documents: list[str], chunks: list[str], provider: str | None = None
) -> list[tuple[str, bool]]:
    """
    Generate contextual information for multiple chunks in a single API call to avoid rate limiting.

    This processes ALL chunks passed to it in a single API call.
    The caller should batch appropriately (e.g., 10 chunks at a time).

    Args:
        full_documents: List of complete document texts
        chunks: List of specific chunks to generate context for
        provider: Optional provider override

    Returns:
        List of tuples containing:
        - The contextual text that situates the chunk within the document
        - Boolean indicating if contextual embedding was performed
    """
    try:
        async with get_llm_client(provider=provider) as client:
            # Get model choice from credential service (RAG setting)
            model_choice = await _get_model_choice(provider)

            # Build batch prompt for ALL chunks at once
            batch_prompt = "Process the following chunks and provide contextual information for each:\\n\\n"

            for i, (doc, chunk) in enumerate(zip(full_documents, chunks, strict=False)):
                # Use 10k chars per doc in batch mode to stay within reasonable token limits
                doc_preview = doc[:10000] if len(doc) > 10000 else doc
                batch_prompt += f"CHUNK {i + 1}:\\n"
                batch_prompt += f"<document_preview>\\n{doc_preview}\\n</document_preview>\\n"
                batch_prompt += f"<chunk>\\n{chunk[:1000]}\\n</chunk>\\n\\n"  # Increased chunk preview

            batch_prompt += "For each chunk, provide a short succinct context to situate it within the overall document for improving search retrieval. Answer only with the succinct context. Format your response as:\\nCHUNK 1: [context]\\nCHUNK 2: [context]\\netc."

            from ..prompt_service import prompt_service
            default_batch_prompt = "You are a professional librarian that generates high-signal contextual information for RAG retrieval."
            system_prompt = prompt_service.get_prompt("EMBED_CONTEXT_GENERATOR", default_batch_prompt)

            # Make single API call for ALL chunks
            response = await client.chat.completions.create(
                model=model_choice,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": batch_prompt},
                ],
                temperature=0.1,
                max_tokens=200 * len(chunks),  # Increased limit
            )

            # Parse response
            response_text = response.choices[0].message.content

            # Extract contexts from response
            lines = response_text.strip().split("\\n")
            chunk_contexts = {}

            for line in lines:
                if line.strip().startswith("CHUNK"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        chunk_num = int(parts[0].strip().split()[1]) - 1
                        context = parts[1].strip()
                        chunk_contexts[chunk_num] = context

            # Build results
            results = []
            for i, chunk in enumerate(chunks):
                if i in chunk_contexts:
                    # Combine context with full chunk (not truncated)
                    contextual_text = chunk_contexts[i] + "\\n\\n" + chunk
                    results.append((contextual_text, True))
                else:
                    results.append((chunk, False))

            return results

    except openai.RateLimitError as e:
        if "insufficient_quota" in str(e):
            search_logger.warning(f"⚠️ QUOTA EXHAUSTED in contextual embeddings: {e}")
            search_logger.warning("OpenAI quota exhausted - proceeding without contextual embeddings")
        else:
            search_logger.warning(f"Rate limit hit in contextual embeddings batch: {e}")
            search_logger.warning("Rate limit hit - proceeding without contextual embeddings for this batch")
        # Return non-contextual for all chunks
        return [(chunk, False) for chunk in chunks]

    except Exception as e:
        search_logger.error(f"Error in contextual embedding batch: {e}")
        # Return non-contextual for all chunks
        return [(chunk, False) for chunk in chunks]
