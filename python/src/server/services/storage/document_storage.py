"""
Document Storage Facade

Provides the main entry point for document and code storage operations.
Consolidates responsibilities previously split between document_storage_service.py
and crawling/document_storage_operations.py.
"""

import asyncio
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

from src.server.config.logfire_config import safe_logfire_error, safe_logfire_info, safe_span, search_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.services.credential_service import credential_service
from src.server.services.embeddings.contextual_embedding_service import generate_contextual_embeddings_batch
from src.server.services.embeddings.embedding_service import create_embeddings_batch
from src.server.services.source_management_service import extract_source_summary, update_source_info

from .chunking_utils import ChunkingUtils
from .progress_tracker import ProgressTracker
from .repositories.document_repo import DocumentRepository


class DocumentStorageFacade(BaseRepository):
    """Facade for all document storage and processing operations."""

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client)
        self.repo = DocumentRepository(self.supabase_client)
        self.chunking_utils = ChunkingUtils(self.supabase_client)
        from src.server.services.code_extraction.code_extraction_service import CodeExtractionService

        self.code_extraction_service = CodeExtractionService(self.supabase_client)

    async def store_documents(
        self,
        crawl_results: list[dict],
        request: dict[str, Any],
        crawl_type: str,
        original_source_id: str,
        progress_callback: Callable | None = None,
        cancellation_check: Callable | None = None,
        source_url: str | None = None,
        source_display_name: str | None = None,
    ) -> dict[str, Any]:
        """
        Process crawled documents, chunk them, generate embeddings, and store them.
        """
        # 1. Chunking Phase (Pure Logic)
        (
            all_urls,
            all_chunk_numbers,
            all_contents,
            all_metadatas,
            source_word_counts,
            url_to_full_document,
            processed_docs,
        ) = await self.chunking_utils.prepare_document_chunks(
            crawl_results, request, crawl_type, original_source_id, cancellation_check
        )

        # 2. Source Record Phase
        if all_contents and all_metadatas:
            await self._create_source_records(
                all_metadatas, all_contents, source_word_counts, request, source_url, source_display_name
            )

        avg_chunks = (len(all_contents) / processed_docs) if processed_docs > 0 else 0.0
        safe_logfire_info(
            f"Document storage | processed={processed_docs}/{len(crawl_results)} | chunks={len(all_contents)} | avg_chunks={avg_chunks:.1f}"
        )

        # 3. Storage and Embeddings Phase
        storage_stats = await self._add_documents_to_supabase(
            urls=all_urls,
            chunk_numbers=all_chunk_numbers,
            contents=all_contents,
            metadatas=all_metadatas,
            url_to_full_document=url_to_full_document,
            progress_callback=progress_callback,
            cancellation_check=cancellation_check,
        )

        return {
            "chunk_count": len(all_contents),
            "chunks_stored": storage_stats.get("chunks_stored", 0),
            "total_word_count": sum(source_word_counts.values()),
            "url_to_full_document": url_to_full_document,
            "source_id": original_source_id,
        }

    async def store_code_examples(
        self,
        crawl_results: list[dict],
        url_to_full_document: dict[str, str],
        source_id: str,
        progress_callback: Callable | None = None,
        start_progress: int = 85,
        end_progress: int = 95,
        cancellation_check: Callable | None = None,
    ) -> int:
        """
        Delegates to CodeExtractionService to extract and store code snippets.
        """
        return await self.code_extraction_service.extract_and_store_code_examples(
            crawl_results,
            url_to_full_document,
            source_id,
            progress_callback,
            start_progress,
            end_progress,
            cancellation_check,
        )

    async def _add_documents_to_supabase(
        self,
        urls: list[str],
        chunk_numbers: list[int],
        contents: list[str],
        metadatas: list[dict[str, Any]],
        url_to_full_document: dict[str, str],
        batch_size: int | None = None,
        progress_callback: Callable | None = None,
        cancellation_check: Callable | None = None,
    ) -> dict[str, int]:
        """Internal method handling DB ingestion, deletion, and embeddings."""
        tracker = ProgressTracker(progress_callback)

        with safe_span("add_documents_to_supabase", total_documents=len(contents), batch_size=batch_size) as span:
            try:
                rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
                if batch_size is None:
                    batch_size = int(rag_settings.get("DOCUMENT_STORAGE_BATCH_SIZE", "50"))
                delete_batch_size = int(rag_settings.get("DELETE_BATCH_SIZE", "50"))
            except Exception as e:
                search_logger.warning(f"Failed to load storage settings: {e}, using defaults")
                batch_size = batch_size or 50
                delete_batch_size = 50

            # Delete existing records using Repository
            await self.repo.delete_existing_urls_in_batches(urls, delete_batch_size, cancellation_check)

            # Check contextual embeddings
            try:
                use_contextual_embeddings = await credential_service.get_credential(
                    "USE_CONTEXTUAL_EMBEDDINGS", "false", decrypt=True
                )
                if isinstance(use_contextual_embeddings, str):
                    use_contextual_embeddings = use_contextual_embeddings.lower() == "true"
            except Exception:
                from src.server.services.settings_service import SettingsService
                use_contextual_embeddings = str(SettingsService().get_setting("USE_CONTEXTUAL_EMBEDDINGS") or "false").lower() == "true"

            completed_batches = 0
            total_batches = (len(contents) + batch_size - 1) // batch_size
            total_chunks_stored = 0

            for batch_num, i in enumerate(range(0, len(contents), batch_size), 1):
                if cancellation_check:
                    cancellation_check()

                batch_end = min(i + batch_size, len(contents))
                batch_urls = urls[i:batch_end]
                batch_chunk_numbers = chunk_numbers[i:batch_end]
                batch_contents = contents[i:batch_end]
                batch_metadatas = metadatas[i:batch_end]

                current_progress = int((completed_batches / total_batches) * 100)

                # Contextual Embeddings Phase
                contextual_contents = batch_contents
                max_workers = 1
                if use_contextual_embeddings:
                    from src.server.services.settings_service import SettingsService
                    max_workers = int(SettingsService().get_setting("CONTEXTUAL_EMBEDDINGS_MAX_WORKERS") or "4")
                    full_documents = [url_to_full_document.get(u, "") for u in batch_urls]
                    try:
                        sub_results = await generate_contextual_embeddings_batch(full_documents, batch_contents)
                        contextual_contents = []
                        for idx, (contextual_text, success) in enumerate(sub_results):
                            contextual_contents.append(contextual_text)
                            if success:
                                batch_metadatas[idx]["contextual_embedding"] = True
                    except Exception as e:
                        search_logger.error(f"Contextual embedding error: {e}")

                # Standard Embedding Phase
                async def progress_wrap(msg, pct, cp=current_progress, bn=batch_num):
                    await tracker.embedding_progress_wrapper(msg, pct, cp, bn)

                result = await create_embeddings_batch(
                    contextual_contents, progress_callback=progress_wrap if progress_callback else None
                )

                if not result.embeddings:
                    raise Exception(f"Skipping batch {batch_num} - no successful embeddings")

                batch_data = []
                for _j, (embedding, text) in enumerate(zip(result.embeddings, result.texts_processed, strict=False)):
                    try:
                        orig_idx = contextual_contents.index(text)
                    except ValueError:
                        continue

                    source_id = batch_metadatas[orig_idx].get("source_id")
                    if not source_id:
                        parsed = urlparse(batch_urls[orig_idx])
                        source_id = parsed.netloc or parsed.path

                    batch_data.append(
                        {
                            "url": batch_urls[orig_idx],
                            "chunk_number": batch_chunk_numbers[orig_idx],
                            "content": text,
                            "metadata": {"chunk_size": len(text), **batch_metadatas[orig_idx]},
                            "source_id": source_id,
                            "embedding": embedding,
                        }
                    )

                # DB Insertion Phase using Repository
                max_retries = 3
                retry_delay = 1.0
                for retry in range(max_retries):
                    if cancellation_check:
                        cancellation_check()
                    try:
                        self.repo.insert_document_batch(batch_data)
                        total_chunks_stored += len(batch_data)
                        completed_batches += 1
                        new_progress = (
                            100
                            if completed_batches == total_batches
                            else int((completed_batches / total_batches) * 100)
                        )

                        await tracker.report_progress(
                            f"Completed batch {batch_num}/{total_batches} ({len(batch_data)} chunks)",
                            new_progress,
                            {
                                "current_batch": batch_num,
                                "total_batches": total_batches,
                                "completed_batches": completed_batches,
                                "active_workers": max_workers,
                            },
                        )
                        break
                    except Exception as e:
                        if retry < max_retries - 1:
                            await asyncio.sleep(retry_delay)
                            retry_delay *= 2
                        else:
                            search_logger.error(f"Failed to insert batch: {e}")

                if i + batch_size < len(contents):
                    await asyncio.sleep(0.1)

            await tracker.report_final_progress(len(contents), total_batches)

            span.set_attribute("success", True)
            span.set_attribute("total_processed", len(contents))
            span.set_attribute("total_stored", total_chunks_stored)
            return {"chunks_stored": total_chunks_stored}

    async def _create_source_records(
        self,
        all_metadatas: list[dict],
        all_contents: list[str],
        source_word_counts: dict[str, int],
        request: dict[str, Any],
        source_url: str | None = None,
        source_display_name: str | None = None,
    ):
        """Internal helper to create source records via Repositories and external services."""
        unique_source_ids = set()
        source_id_contents: dict[str, list[str]] = {}

        for i, metadata in enumerate(all_metadatas):
            source_id = metadata["source_id"]
            unique_source_ids.add(source_id)
            if source_id not in source_id_contents:
                source_id_contents[source_id] = []
            source_id_contents[source_id].append(all_contents[i])

        for source_id in unique_source_ids:
            source_contents = source_id_contents[source_id]
            combined_content = ""
            for chunk in source_contents[:3]:
                if len(combined_content) + len(chunk) < 15000:
                    combined_content += " " + chunk
                else:
                    break

            try:
                summary = await extract_source_summary(source_id, combined_content)
            except Exception as e:
                search_logger.error(f"Failed to generate AI summary for '{source_id}'", exc_info=True)
                safe_logfire_error(f"Failed to generate AI summary for '{source_id}': {str(e)}, using fallback")
                summary = f"Documentation from {source_id} - {len(source_contents)} pages crawled"

            try:
                await update_source_info(
                    client=self.supabase_client,
                    source_id=source_id,
                    summary=summary,
                    word_count=source_word_counts[source_id],
                    content=combined_content,
                    knowledge_type=request.get("knowledge_type", "documentation"),
                    tags=request.get("tags", []),
                    update_frequency=0,
                    original_url=request.get("url"),
                    source_url=source_url,
                    source_display_name=source_display_name,
                )
                safe_logfire_info(f"Successfully created/updated source record for '{source_id}'")
            except Exception as e:
                search_logger.error(f"Failed to create/update source record for '{source_id}'", exc_info=True)
                safe_logfire_error(f"Failed to create/update source record for '{source_id}': {str(e)}")
                safe_logfire_info(f"Attempting fallback source creation for '{source_id}'")
                fallback_data = {
                    "source_id": source_id,
                    "title": source_id,
                    "summary": summary,
                    "total_word_count": source_word_counts[source_id],
                    "metadata": {
                        "knowledge_type": request.get("knowledge_type", "documentation"),
                        "tags": request.get("tags", []),
                        "auto_generated": True,
                        "fallback_creation": True,
                        "original_url": request.get("url"),
                    },
                }
                if source_url:
                    fallback_data["source_url"] = source_url
                if source_display_name:
                    fallback_data["source_display_name"] = source_display_name

                success, _ = self.repo.upsert_source_fallback(source_id, fallback_data)
                if not success:
                    raise Exception(f"Failed fallback creation for {source_id}") from None

        for source_id in unique_source_ids:
            success, _ = self.repo.verify_source_exists(source_id)
            if not success:
                raise Exception(f"Source verification failed for {source_id}")
