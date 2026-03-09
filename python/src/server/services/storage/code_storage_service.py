"""
Code Storage Service

Handles extraction and storage of code examples from documents.
"""

import os
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

from supabase import Client

from ...config.logfire_config import search_logger
from ..embeddings.contextual_embedding_service import generate_contextual_embeddings_batch
from ..embeddings.embedding_service import create_embeddings_batch


async def generate_code_summaries_batch(
    self, code_blocks: list[dict[str, Any]], provider: str | None = None
) -> list[dict[str, str]]:
    """
    Generate summaries for multiple code blocks.
    Delegates to summarization submodule.
    """
    from .code.summarization import generate_code_summaries_batch_logic
    return await generate_code_summaries_batch_logic(self, code_blocks, provider)


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

    Args:
        client: Supabase client
        urls: List of URLs
        chunk_numbers: List of chunk numbers
        code_examples: List of code example contents
        summaries: List of code example summaries
        metadatas: List of metadata dictionaries
        batch_size: Size of each batch for insertion
        url_to_full_document: Optional mapping of URLs to full document content
        progress_callback: Optional async callback for progress updates
    """
    if not urls:
        return

    # Delete existing records for these URLs
    unique_urls = list(set(urls))
    for url in unique_urls:
        try:
            client.table("archon_code_examples").delete().eq("url", url).execute()
        except Exception as e:
            search_logger.error(f"Error deleting existing code examples for {url}: {e}")

    # Check if contextual embeddings are enabled
    try:
        from ..credential_service import credential_service

        use_contextual_embeddings = credential_service._cache.get("USE_CONTEXTUAL_EMBEDDINGS")
        if isinstance(use_contextual_embeddings, str):
            use_contextual_embeddings = use_contextual_embeddings.lower() == "true"
        elif isinstance(use_contextual_embeddings, dict) and use_contextual_embeddings.get(
            "is_encrypted"
        ):
            # Handle encrypted value
            encrypted_value = use_contextual_embeddings.get("encrypted_value")
            if encrypted_value:
                try:
                    decrypted = credential_service._decrypt_value(encrypted_value)
                    use_contextual_embeddings = decrypted.lower() == "true"
                except Exception:
                    use_contextual_embeddings = False
            else:
                use_contextual_embeddings = False
        else:
            use_contextual_embeddings = bool(use_contextual_embeddings)
    except Exception:
        # Fallback to environment variable
        use_contextual_embeddings = (
            os.getenv("USE_CONTEXTUAL_EMBEDDINGS", "false").lower() == "true"
        )

    search_logger.info(
        f"Using contextual embeddings for code examples: {use_contextual_embeddings}"
    )

    # Process in batches
    total_items = len(urls)
    for i in range(0, total_items, batch_size):
        batch_end = min(i + batch_size, total_items)
        batch_texts = []
        batch_metadatas_for_batch = metadatas[i:batch_end]

        # Create combined texts for embedding (code + summary)
        combined_texts = []
        for j in range(i, batch_end):
            # Validate inputs
            code = code_examples[j] if isinstance(code_examples[j], str) else str(code_examples[j])
            summary = summaries[j] if isinstance(summaries[j], str) else str(summaries[j])

            if not code:
                search_logger.warning(f"Empty code at index {j}, skipping...")
                continue

            combined_text = f"{code}\n\nSummary: {summary}"
            combined_texts.append(combined_text)

        # Apply contextual embeddings if enabled
        if use_contextual_embeddings and url_to_full_document:
            # Get full documents for context
            full_documents = []
            for j in range(i, batch_end):
                url = urls[j]
                full_doc = url_to_full_document.get(url, "")
                full_documents.append(full_doc)

            # Generate contextual embeddings
            contextual_results = await generate_contextual_embeddings_batch(
                full_documents, combined_texts
            )

            # Process results
            for j, (contextual_text, success) in enumerate(contextual_results):
                batch_texts.append(contextual_text)
                if success and j < len(batch_metadatas_for_batch):
                    batch_metadatas_for_batch[j]["contextual_embedding"] = True
        else:
            # Use original combined texts
            batch_texts = combined_texts

        # Create embeddings for the batch
        result = await create_embeddings_batch(batch_texts)

        # Log any failures
        if result.has_failures:
            search_logger.error(
                f"Failed to create {result.failure_count} code example embeddings. "
                f"Successful: {result.success_count}"
            )

        # Use only successful embeddings
        valid_embeddings = result.embeddings
        successful_texts = result.texts_processed

        if not valid_embeddings:
            search_logger.warning("Skipping batch - no successful embeddings created")
            continue

        # Prepare batch data - only for successful embeddings
        batch_data = []
        for _j, (embedding, text) in enumerate(
            zip(valid_embeddings, successful_texts, strict=False)
        ):
            # Find the original index
            orig_idx = None
            for k, orig_text in enumerate(batch_texts):
                if orig_text == text:
                    orig_idx = k
                    break

            if orig_idx is None:
                search_logger.warning("Could not map embedding back to original code example")
                continue

            idx = i + orig_idx  # Get the global index

            # Use source_id from metadata if available, otherwise extract from URL
            source_id = None
            if metadatas[idx] is not None and "source_id" in metadatas[idx]:
                source_id = metadatas[idx]["source_id"]

            if source_id is None:
                parsed_url = urlparse(urls[idx])
                source_id = parsed_url.netloc or parsed_url.path

            batch_data.append({
                "url": urls[idx],
                "chunk_number": chunk_numbers[idx],
                "content": code_examples[idx],
                "summary": summaries[idx],
                "metadata": metadatas[idx],  # Store as JSON object, not string
                "source_id": source_id,
                "embedding": embedding,
            })

        # Insert batch into Supabase with retry logic
        max_retries = 3
        retry_delay = 1.0

        for retry in range(max_retries):
            try:
                client.table("archon_code_examples").insert(batch_data).execute()
                # Success - break out of retry loop
                break
            except Exception as e:
                if retry < max_retries - 1:
                    search_logger.warning(
                        f"Error inserting batch into Supabase (attempt {retry + 1}/{max_retries}): {e}"
                    )
                    search_logger.info(f"Retrying in {retry_delay} seconds...")
                    import time

                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    # Final attempt failed
                    search_logger.error(f"Failed to insert batch after {max_retries} attempts: {e}")
                    # Optionally, try inserting records one by one as a last resort
                    search_logger.info("Attempting to insert records individually...")
                    successful_inserts = 0
                    for record in batch_data:
                        try:
                            client.table("archon_code_examples").insert(record).execute()
                            successful_inserts += 1
                        except Exception as individual_error:
                            search_logger.error(
                                f"Failed to insert individual record for URL {record['url']}: {individual_error}"
                            )

                    if successful_inserts > 0:
                        search_logger.info(
                            f"Successfully inserted {successful_inserts}/{len(batch_data)} records individually"
                        )

        search_logger.info(
            f"Inserted batch {i // batch_size + 1} of {(total_items + batch_size - 1) // batch_size} code examples"
        )

        # Report progress if callback provided
        if progress_callback:
            batch_num = i // batch_size + 1
            total_batches = (total_items + batch_size - 1) // batch_size
            progress_percentage = int((batch_num / total_batches) * 100)
            await progress_callback({
                "status": "code_storage",
                "percentage": progress_percentage,
                "log": f"Stored batch {batch_num}/{total_batches} of code examples",
                # Stage-specific batch fields to prevent contamination with document storage
                "code_current_batch": batch_num,
                "code_total_batches": total_batches,
                # Keep generic fields for backward compatibility
                "batch_number": batch_num,
                "total_batches": total_batches,
            })

    # Report final completion at 100% after all batches are done
    if progress_callback and total_items > 0:
        await progress_callback({
            "status": "code_storage",
            "percentage": 100,
            "log": f"Code storage completed. Stored {total_items} code examples.",
            "total_items": total_items,
            # Keep final batch info for code storage completion
            "code_total_batches": (total_items + batch_size - 1) // batch_size,
            "code_current_batch": (total_items + batch_size - 1) // batch_size,
        })
