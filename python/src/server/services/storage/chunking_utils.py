import asyncio
from collections.abc import Callable
from typing import Any

from src.server.config.logfire_config import get_logger, safe_logfire_info

logger = get_logger(__name__)


class ChunkingUtils:
    """Handles logic for splitting markdown documents into chunks without DB interaction."""

    def __init__(self, supabase_client: Any = None) -> None:
        from src.server.services.storage.storage_services import DocumentStorageService

        self.doc_storage_service = DocumentStorageService(supabase_client)

    async def prepare_document_chunks(
        self,
        crawl_results: list[dict],
        request: dict[str, Any],
        crawl_type: str,
        original_source_id: str,
        cancellation_check: Callable | None = None,
    ) -> tuple[list[str], list[int], list[str], list[dict], dict[str, int], dict[str, str], int]:
        """
        Splits documents into chunks and prepares metadatas.

        Returns:
            (all_urls, all_chunk_numbers, all_contents, all_metadatas, source_word_counts, url_to_full_document, processed_docs)
        """
        all_urls = []
        all_chunk_numbers = []
        all_contents = []
        all_metadatas = []
        source_word_counts: dict[str, int] = {}
        url_to_full_document = {}
        processed_docs = 0

        for doc_index, doc in enumerate(crawl_results):
            if cancellation_check:
                cancellation_check()

            doc_url = (doc.get("url") or "").strip()
            markdown_content = (doc.get("markdown") or "").strip()

            if not markdown_content or not doc_url:
                logger.debug(f"Skipping document {doc_index}: empty {'URL' if not doc_url else 'content'}")
                continue

            processed_docs += 1
            url_to_full_document[doc_url] = markdown_content

            # CHUNK THE CONTENT
            chunks = await self.doc_storage_service.smart_chunk_text_async(markdown_content, chunk_size=5000)

            source_id = original_source_id
            safe_logfire_info(f"Using original source_id '{source_id}' for URL '{doc_url}'")

            for i, chunk in enumerate(chunks):
                if cancellation_check and i % 10 == 0:
                    cancellation_check()

                all_urls.append(doc_url)
                all_chunk_numbers.append(i)
                all_contents.append(chunk)

                word_count = len(chunk.split())
                metadata = {
                    "url": doc_url,
                    "title": doc.get("title", ""),
                    "description": doc.get("description", ""),
                    "source_id": source_id,
                    "knowledge_type": request.get("knowledge_type", "documentation"),
                    "crawl_type": crawl_type,
                    "word_count": word_count,
                    "char_count": len(chunk),
                    "chunk_index": i,
                    "tags": request.get("tags", []),
                }
                all_metadatas.append(metadata)

                source_word_counts[source_id] = source_word_counts.get(source_id, 0) + word_count

                if i > 0 and i % 10 == 0:
                    await asyncio.sleep(0)

            if doc_index > 0 and doc_index % 5 == 0:
                await asyncio.sleep(0)

        return (
            all_urls,
            all_chunk_numbers,
            all_contents,
            all_metadatas,
            source_word_counts,
            url_to_full_document,
            processed_docs,
        )
