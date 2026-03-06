"""
Page Storage Operations

Handles the storage of complete documentation pages in the archon_page_metadata table.
Pages are stored BEFORE chunking to maintain full context for agent retrieval.
"""

from typing import Any

from src.server.repositories.base_repository import BaseRepository

from ...config.logfire_config import get_logger, safe_logfire_error, safe_logfire_info
from .helpers.llms_full_parser import parse_llms_full_sections

logger = get_logger(__name__)


class PageStorageOperations(BaseRepository):
    """
    Handles page storage operations for crawled content.

    Pages are stored in the archon_page_metadata table with full content and metadata.
    This enables agents to retrieve complete documentation pages instead of just chunks.
    """

    def __init__(self, supabase_client=None):
        """
        Initialize page storage operations.

        Args:
            supabase_client: The Supabase client for database operations
        """
        super().__init__(supabase_client)

    async def store_pages(
        self,
        crawl_results: list[dict],
        source_id: str,
        request: dict[str, Any],
        crawl_type: str,
    ) -> dict[str, str]:
        """
        Store pages in archon_page_metadata table from regular crawl results.

        Args:
            crawl_results: List of crawled documents with url, markdown, title, etc.
            source_id: The source ID these pages belong to
            request: The original crawl request with knowledge_type, tags, etc.
            crawl_type: Type of crawl performed (sitemap, url, link_collection, etc.)

        Returns:
            {url: page_id} mapping for FK references in chunks
        """
        safe_logfire_info(
            f"store_pages called | source_id={source_id} | crawl_type={crawl_type} | num_results={len(crawl_results)}"
        )

        url_to_page_id: dict[str, str] = {}
        pages_to_insert: list[dict[str, Any]] = []

        for doc in crawl_results:
            url = doc.get("url", "").strip()
            markdown = doc.get("markdown", "").strip()

            # Skip documents with empty content or missing URLs
            if not url or not markdown:
                continue

            # Prepare page record
            word_count = len(markdown.split())
            char_count = len(markdown)

            page_record = {
                "source_id": source_id,
                "url": url,
                "full_content": markdown,
                "section_title": None,  # Regular page, not a section
                "section_order": 0,
                "word_count": word_count,
                "char_count": char_count,
                "chunk_count": 0,  # Will be updated after chunking
                "metadata": {
                    "knowledge_type": request.get("knowledge_type", "documentation"),
                    "crawl_type": crawl_type,
                    "page_type": "documentation",
                    "tags": request.get("tags", []),
                },
            }
            pages_to_insert.append(page_record)

        # Batch upsert pages
        if pages_to_insert:
            safe_logfire_info(
                f"Upserting {len(pages_to_insert)} pages into archon_page_metadata table"
            )
            query = self.supabase_client.table("archon_page_metadata").upsert(pages_to_insert, on_conflict="url")
            success, response = self.execute_query(
                query.execute,
                error_context=f"Failed to upsert pages for source {source_id}",
                require_data=True
            )

            if success and response.get("data"):
                # Build url → page_id mapping
                for page in response["data"]:
                    url_to_page_id[page["url"]] = page["id"]

                safe_logfire_info(
                    f"Successfully stored {len(url_to_page_id)}/{len(pages_to_insert)} pages in archon_page_metadata"
                )
            else:
                safe_logfire_error(
                    f"Error upserting pages | source_id={source_id} | attempted={len(pages_to_insert)} | error={response.get('error')}"
                )
                # Don't raise - allow chunking to continue

        return url_to_page_id

    async def store_llms_full_sections(
        self,
        base_url: str,
        content: str,
        source_id: str,
        request: dict[str, Any],
        crawl_type: str = "llms_full",
    ) -> dict[str, str]:
        """
        Store llms-full.txt sections as separate pages.

        Each H1 section gets its own page record with a synthetic URL.

        Args:
            base_url: Base URL of the llms-full.txt file
            content: Full text content of the file
            source_id: The source ID these sections belong to
            request: The original crawl request
            crawl_type: Type of crawl (defaults to "llms_full")

        Returns:
            {url: page_id} mapping for FK references in chunks
        """
        url_to_page_id: dict[str, str] = {}

        # Parse sections from content
        sections = parse_llms_full_sections(content, base_url)

        if not sections:
            logger.warning(f"No sections found in llms-full.txt file: {base_url}")
            return url_to_page_id

        safe_logfire_info(
            f"Parsed {len(sections)} sections from llms-full.txt file: {base_url}"
        )

        # Prepare page records for each section
        pages_to_insert: list[dict[str, Any]] = []

        for section in sections:
            page_record = {
                "source_id": source_id,
                "url": section.url,
                "full_content": section.content,
                "section_title": section.section_title,
                "section_order": section.section_order,
                "word_count": section.word_count,
                "char_count": len(section.content),
                "chunk_count": 0,  # Will be updated after chunking
                "metadata": {
                    "knowledge_type": request.get("knowledge_type", "documentation"),
                    "crawl_type": crawl_type,
                    "page_type": "llms_full_section",
                    "tags": request.get("tags", []),
                    "section_metadata": {
                        "section_title": section.section_title,
                        "section_order": section.section_order,
                        "base_url": base_url,
                    },
                },
            }
            pages_to_insert.append(page_record)

        # Batch upsert pages
        if pages_to_insert:
            safe_logfire_info(
                f"Upserting {len(pages_to_insert)} section pages into archon_page_metadata"
            )
            query = self.supabase_client.table("archon_page_metadata").upsert(pages_to_insert, on_conflict="url")
            success, response = self.execute_query(
                query.execute,
                error_context=f"Failed to upsert sections for {base_url}",
                require_data=True
            )

            if success and response.get("data"):
                # Build url → page_id mapping
                for page in response["data"]:
                    url_to_page_id[page["url"]] = page["id"]

                safe_logfire_info(
                    f"Successfully stored {len(url_to_page_id)}/{len(pages_to_insert)} section pages"
                )
            else:
                safe_logfire_error(
                    f"Error upserting sections | base_url={base_url} | attempted={len(pages_to_insert)} | error={response.get('error')}"
                )
                # Don't raise - allow process to continue

        return url_to_page_id

    async def update_page_chunk_count(self, page_id: str, chunk_count: int) -> None:
        """
        Update the chunk_count field for a page after chunking is complete.

        Args:
            page_id: The UUID of the page to update
            chunk_count: Number of chunks created from this page
        """
        query = self.supabase_client.table("archon_page_metadata").update(
            {"chunk_count": chunk_count}
        ).eq("id", page_id)

        success, response = self.execute_query(
            query.execute,
            error_context=f"Failed to update chunk_count for page {page_id}",
            require_data=True  # Ensure update was successful? Wait, update returns data. Let's say False to be safe if require_data should be False for an update that might just affect 1 row, but Supabase updates return the updated rows.
        )

        if success:
            safe_logfire_info(f"Updated chunk_count={chunk_count} for page_id={page_id}")
        else:
            logger.warning(
                f"Database error updating chunk_count for page {page_id}: {response.get('error')}"
            )
