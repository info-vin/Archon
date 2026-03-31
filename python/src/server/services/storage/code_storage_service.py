"""
Code Storage Service

Handles storage operations for extracted code examples, including
contextual embeddings and AI summaries.
"""

import os
from collections.abc import Callable
from typing import Any

from supabase import Client

from src.server.config.logfire_config import search_logger

from ..embeddings.contextual_embedding_service import generate_contextual_embeddings_batch
from ..embeddings.embedding_service import EmbeddingBatchResult, create_embeddings_batch


def _get_model_choice() -> str:
    """Get MODEL_CHOICE with direct fallback (Facade)."""
    from .code.summarization import _get_model_choice_logic

    return _get_model_choice_logic()


def _get_max_workers() -> int:
    """Get max workers logic (Facade)."""
    return int(os.getenv("CONTEXTUAL_EMBEDDINGS_MAX_WORKERS", "3"))


async def generate_code_summaries_batch(
    code_blocks: list[dict[str, Any]],
    max_workers: int | None = None,
    progress_callback: Any = None,
    provider: str | None = None,
) -> list[dict[str, str]]:
    """
    Generate summaries for multiple code blocks.
    Delegates to summarization submodule.
    Kept as a module-level function for backward compatibility.
    """
    from .code.summarization import generate_code_summaries_batch_logic

    return await generate_code_summaries_batch_logic(None, code_blocks, max_workers, progress_callback, provider)


def extract_code_blocks(markdown_content: str, min_length: int | None = None) -> list[dict[str, Any]]:
    """
    Extract code blocks from markdown content.
    Delegates to extraction submodule.
    """
    from .code.extraction import extract_code_blocks_logic

    return extract_code_blocks_logic(markdown_content, min_length)


def generate_code_example_summary(
    code: str, context_before: str, context_after: str, language: str = "", provider: str | None = None
) -> dict[str, str]:
    """
    Generate a summary and name for a code example.
    Delegates to summarization submodule.
    """
    from .code.summarization import generate_code_example_summary_logic

    return generate_code_example_summary_logic(code, context_before, context_after, language, provider)


async def add_code_examples_to_supabase(
    client: Client,
    urls: list[str],
    chunk_numbers: list[int],
    code_examples: list[str],
    summaries: list[str],
    metadatas: list[dict[str, Any]],
    batch_size: int = 20,
    url_to_full_document: dict[str, str] | None = None,
    progress_callback: Callable | None = None,
    provider: str | None = None,
):
    """
    Add code examples to the Supabase code_examples table in batches.
    """
    total_examples = len(code_examples)
    if total_examples == 0:
        return

    # Check for contextual embeddings setting
    from src.server.services.credential_service import credential_service

    enable_contextual_val = await credential_service.get_credential("ENABLE_CONTEXTUAL_EMBEDDINGS", "false")
    enable_contextual = str(enable_contextual_val).lower() == "true"

    context_texts: list[str] | None = None
    if enable_contextual and url_to_full_document:
        search_logger.info("Generating context for code examples...")
        full_docs = [url_to_full_document.get(url, "") for url in urls]
        context_results = await generate_contextual_embeddings_batch(full_docs, code_examples, provider=provider)
        context_texts = [res[0] for res in context_results]

    for i in range(0, total_examples, batch_size):
        batch_end = min(i + batch_size, total_examples)
        batch_examples = code_examples[i:batch_end]

        batch_result: EmbeddingBatchResult = await create_embeddings_batch(batch_examples, progress_callback=None)

        if batch_result.success_count == 0:
            search_logger.error(f"Failed to generate embeddings for batch {i // batch_size}")
            continue

        embeddings = batch_result.embeddings

        batch_data = []
        for j, (example, embedding, summary, url, chunk_num, meta) in enumerate(
            zip(
                batch_examples,
                embeddings,
                summaries[i:batch_end],
                urls[i:batch_end],
                chunk_numbers[i:batch_end],
                metadatas[i:batch_end],
                strict=False,
            )
        ):
            row = {
                "source_url": url,
                "chunk_number": chunk_num,
                "code_content": example,
                "embedding": embedding,
                "summary": summary,
                "metadata": meta,
            }
            if context_texts:
                row["contextual_embedding"] = context_texts[i + j]
            batch_data.append(row)

        try:
            client.table("code_examples").insert(batch_data).execute()
            if progress_callback:
                await progress_callback(
                    {
                        "status": "storing_code",
                        "log": f"Stored {batch_end}/{total_examples} code examples",
                        "current": batch_end,
                        "total": total_examples,
                    }
                )
        except Exception as e:
            search_logger.error(f"Failed to insert code examples batch: {e}")


class CodeStorageService:
    """
    Facade Service for code storage operations.
    """

    def __init__(self, supabase_client: Client | None = None):
        self.supabase_client = supabase_client

    async def add_code_examples(self, **kwargs):
        client = self.supabase_client
        if client is None:
            from ....utils import get_supabase_client

            client = get_supabase_client()
        return await add_code_examples_to_supabase(client=client, **kwargs)

    async def generate_summaries(self, blocks, max_workers=None, callback=None, provider=None):
        return await generate_code_summaries_batch(blocks, max_workers, callback, provider)
