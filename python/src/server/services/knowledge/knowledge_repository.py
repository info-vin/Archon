"""
Knowledge Repository

Handles database operations for knowledge items, documents, and code examples.
"""

from typing import Any

from src.server.repositories.base_repository import BaseRepository

from ...config.logfire_config import safe_logfire_error


class KnowledgeRepository(BaseRepository):
    """
    Repository for database operations related to knowledge items.
    """

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client)

    async def get_document_counts_batch(self, source_ids: list[str]) -> dict[str, int]:
        """Get document counts for multiple sources."""
        try:
            counts = {}
            for source_id in source_ids:
                success, res = self.execute_query(
                    self.supabase_client.from_("archon_crawled_pages")
                    .select("id", count="exact", head=True)
                    .eq("source_id", source_id),
                    "Fetch document count"
                )
                counts[source_id] = res.get("count", 0) if success else 0
            return counts
        except Exception as e:
            safe_logfire_error(f"Failed to get document counts | error={str(e)}")
            return dict.fromkeys(source_ids, 0)

    async def get_code_example_counts_batch(self, source_ids: list[str]) -> dict[str, int]:
        """Get code example counts for multiple sources."""
        try:
            counts = {}
            for source_id in source_ids:
                success, res = self.execute_query(
                    self.supabase_client.from_("archon_code_examples")
                    .select("id", count="exact", head=True)
                    .eq("source_id", source_id),
                    "Fetch code example count"
                )
                counts[source_id] = res.get("count", 0) if success else 0
            return counts
        except Exception as e:
            safe_logfire_error(f"Failed to get code example counts | error={str(e)}")
            return dict.fromkeys(source_ids, 0)

    async def get_first_urls_batch(self, source_ids: list[str]) -> dict[str, str]:
        """Get first URL for each source in a batch."""
        try:
            success, res = self.execute_query(
                self.supabase_client.from_("archon_crawled_pages")
                .select("source_id, url")
                .in_("source_id", source_ids)
                .order("created_at", desc=False),
                "Fetch first URLs"
            )

            urls = {}
            for item in res.get("data", []) if success else []:
                source_id = item["source_id"]
                if source_id not in urls:
                    urls[source_id] = item["url"]

            for source_id in source_ids:
                if source_id not in urls:
                    urls[source_id] = f"source://{source_id}"

            return urls
        except Exception as e:
            safe_logfire_error(f"Failed to get first URLs | error={str(e)}")
            return {sid: f"source://{sid}" for sid in source_ids}

    async def get_item_chunks(
        self, source_id: str, page: int = 1, per_page: int = 50, domain_filter: str | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """Get document chunks for a specific knowledge item with pagination and filtering."""
        try:
            per_page = max(1, min(per_page, 100))
            page = max(1, page)

            query = self.supabase_client.from_("archon_crawled_pages").select(
                "id, source_id, content, metadata, url", count="exact"
            )
            query = query.eq("source_id", source_id)

            if domain_filter:
                query = query.ilike("url", f"%{domain_filter}%")

            offset = (page - 1) * per_page
            query = query.order("url", desc=False).order("id", desc=False)
            query = query.range(offset, offset + per_page - 1)
            success, res = self.execute_query(query, "Fetch item chunks")

            if not success:
                return False, {"error": res.get("error", "Unknown error")}

            chunks = res.get("data", [])
            total_count = res.get("count", len(chunks))

            return True, {
                "chunks": chunks,
                "pagination": {
                    "total": total_count,
                    "page": page,
                    "per_page": per_page,
                    "total_pages": (total_count + per_page - 1) // per_page if total_count > 0 else 0,
                },
            }
        except Exception as e:
            safe_logfire_error(f"Failed to fetch chunks | source_id={source_id} | error={str(e)}")
            return False, {"error": str(e)}
