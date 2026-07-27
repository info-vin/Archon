import asyncio
from typing import Any

from src.server.config.logfire_config import search_logger


class DocumentRepository:
    """Handles raw database operations for document storage."""

    def __init__(self, supabase_client: Any = None) -> None:
        self.client = supabase_client

    async def delete_existing_urls_in_batches(
        self, urls: list[str], delete_batch_size: int = 50, cancellation_check=None
    ):
        unique_urls = list(set(urls))
        if not unique_urls:
            return

        try:
            for i in range(0, len(unique_urls), delete_batch_size):
                if cancellation_check:
                    cancellation_check()

                batch_urls = unique_urls[i : i + delete_batch_size]
                self.client.table("archon_crawled_pages").delete().in_("url", batch_urls).execute()

                if i + delete_batch_size < len(unique_urls):
                    await asyncio.sleep(0.05)
            search_logger.info(f"Deleted existing records for {len(unique_urls)} URLs in batches")
        except Exception as e:
            search_logger.warning(f"Batch delete failed: {e}. Trying smaller batches as fallback.")
            self._delete_urls_fallback(unique_urls, max(10, delete_batch_size // 5), cancellation_check)

    def _delete_urls_fallback(self, unique_urls: list[str], fallback_batch_size: int, cancellation_check):
        failed_urls = []
        for i in range(0, len(unique_urls), fallback_batch_size):
            if cancellation_check:
                cancellation_check()

            batch_urls = unique_urls[i : i + 10]
            try:
                self.client.table("archon_crawled_pages").delete().in_("url", batch_urls).execute()
                import time

                time.sleep(0.05)
            except Exception as inner_e:
                search_logger.error(f"Error deleting batch of {len(batch_urls)} URLs: {inner_e}")
                failed_urls.extend(batch_urls)

        if failed_urls:
            search_logger.error(f"Failed to delete {len(failed_urls)} URLs")

    def insert_document_batch(self, batch_data: list[dict[str, Any]]) -> bool:
        """Inserts a batch of documents into archon_crawled_pages."""
        try:
            self.client.table("archon_crawled_pages").insert(batch_data).execute()
            return True
        except Exception as e:
            search_logger.error(f"Error inserting batch: {e}")
            raise e

    def upsert_source_fallback(self, source_id: str, fallback_data: dict[str, Any]) -> tuple[bool, Any]:
        """Upserts a source record to archon_sources."""
        try:
            response = self.client.table("archon_sources").upsert(fallback_data).execute()
            return True, response
        except Exception as e:
            return False, {"error": str(e)}

    def verify_source_exists(self, source_id: str) -> tuple[bool, Any]:
        """Checks if a source exists in archon_sources."""
        try:
            response = self.client.table("archon_sources").select("source_id").eq("source_id", source_id).execute()
            return True, {"data": response.data}
        except Exception as e:
            return False, {"error": str(e)}
