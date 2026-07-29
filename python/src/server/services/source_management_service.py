"""
Source Management Service (Refactored)

Entry point for source management. Implementation delegated to logic sub-modules
to maintain a clean, maintainable file size (< 300 lines).
"""

from typing import Any

from src.server.config.logfire_config import get_logger
from src.server.repositories.base_repository import BaseRepository
from src.server.services.client_manager import get_supabase_client

# Re-export logic functions for backward compatibility
from src.server.services.source_management.logic.ai_metadata import (
    extract_source_summary,
    generate_source_title_and_metadata,
)
from src.server.services.source_management.logic.storage_ops import (
    create_source_from_upload_logic,
    update_source_info,
)

logger = get_logger(__name__)

__all__ = [
    "SourceManagementService",
    "extract_source_summary",
    "generate_source_title_and_metadata",
    "update_source_info",
    "create_source_from_upload_logic",
]


class SourceManagementService(BaseRepository):
    """Facade Service for source management operations."""

    def __init__(self, supabase_client: Any = None) -> None:
        client = supabase_client or get_supabase_client()
        super().__init__(client)

    def get_available_sources(self) -> tuple[bool, dict[str, Any]]:
        """Get all available sources from archon_sources."""

        query = self.supabase_client.table("archon_sources").select("*")
        success, result = self.execute_query(
            query_func=query, error_context="Error retrieving sources", require_data=False
        )
        if not success:
            return False, {"error": f"Error retrieving sources: {result['error']}"}

        sources = []
        for row in result["data"] or []:
            sources.append(
                {
                    "source_id": row["source_id"],
                    "title": row.get("title", ""),
                    "summary": row.get("summary", ""),
                    "created_at": row.get("created_at", ""),
                    "updated_at": row.get("updated_at", ""),
                }
            )
        return True, {"sources": sources, "total_count": len(sources)}

    def delete_source(self, source_id: str) -> tuple[bool, dict[str, Any]]:
        """Delete a source and its associations (cascaded manually for precision)."""
        logger.info(f"Starting delete_source for source_id: {source_id}")

        # 1. Pages
        logger.info(f"Deleting from crawled_pages table for source_id: {source_id}")

        query_p = self.supabase_client.table("archon_crawled_pages").delete().eq("source_id", source_id)
        p_ok, p_res = self.execute_query(query_p, "Failed to delete from crawled_pages", False)
        if not p_ok:
            return False, {"error": f"Failed to delete crawled pages: {p_res.get('error')}"}
        pages_deleted = len(p_res["data"] or [])
        logger.info(f"Deleted {pages_deleted} pages from crawled_pages")

        # 2. Code
        logger.info(f"Deleting from code_examples table for source_id: {source_id}")

        query_c = self.supabase_client.table("archon_code_examples").delete().eq("source_id", source_id)
        c_ok, c_res = self.execute_query(query_c, "Failed to delete from code_examples", False)
        if not c_ok:
            return False, {"error": f"Failed to delete code examples: {c_res.get('error')}"}
        code_deleted = len(c_res["data"] or [])
        logger.info(f"Deleted {code_deleted} code examples")

        # 3. Source record
        logger.info(f"Deleting from sources table for source_id: {source_id}")

        query_s = self.supabase_client.table("archon_sources").delete().eq("source_id", source_id)
        s_ok, s_res = self.execute_query(query_s, "Failed to delete from sources", False)
        if not s_ok:
            return False, {"error": f"Failed to delete source: {s_res.get('error')}"}
        source_deleted = len(s_res["data"] or [])
        logger.info(f"Deleted {source_deleted} source records")

        logger.info("Delete operation completed successfully")
        return True, {
            "source_id": source_id,
            "pages_deleted": pages_deleted,
            "code_examples_deleted": code_deleted,
            "source_records_deleted": source_deleted,
        }

    def update_source_metadata(self, source_id: str, **kwargs) -> tuple[bool, dict[str, Any]]:
        """Update source metadata (title, summary, tags, etc)."""
        update_data: dict[str, Any] = {}
        if kwargs.get("title") is not None:
            update_data["title"] = str(kwargs["title"])
        if kwargs.get("summary") is not None:
            update_data["summary"] = str(kwargs["summary"])
        if kwargs.get("word_count") is not None:
            update_data["total_word_count"] = int(kwargs["word_count"])

        if kwargs.get("knowledge_type") or kwargs.get("tags"):

            query_m = self.supabase_client.table("archon_sources").select("metadata").eq("source_id", source_id)
            ok, res = self.execute_query(query_m, "Error getting source metadata", False)
            if not ok:
                return False, {"error": f"Error updating source metadata: {res.get('error')}"}

            metadata = res["data"][0].get("metadata", {}) if res["data"] else {}
            if kwargs.get("knowledge_type"):
                metadata["knowledge_type"] = kwargs["knowledge_type"]
            if kwargs.get("tags"):
                metadata["tags"] = kwargs["tags"]
            update_data["metadata"] = metadata

        if not update_data:
            return False, {"error": "No update data provided"}

        query_u = self.supabase_client.table("archon_sources").update(update_data).eq("source_id", source_id)
        success, result = self.execute_query(query_u, "Error updating source metadata", True)
        if success and result.get("data"):
            return True, {"source_id": source_id, "updated_fields": list(update_data.keys())}
        return False, {"error": f"Source with ID {source_id} not found: {result.get('error', '')}"}

    async def create_source_info(self, source_id: str, content_sample: str, **kwargs) -> tuple[bool, dict[str, Any]]:
        """Delegated creation with behavior parity."""
        try:
            summary = await extract_source_summary(source_id, content_sample)
            await update_source_info(
                self.supabase_client,
                source_id,
                summary,
                kwargs.get("word_count", 0),
                content_sample[:5000],
                kwargs.get("knowledge_type", "technical"),
                kwargs.get("tags", []),
                kwargs.get("update_frequency", 7),
            )
            return True, {
                "source_id": source_id,
                "summary": summary,
                "word_count": kwargs.get("word_count", 0),
                "knowledge_type": kwargs.get("knowledge_type", "technical"),
                "tags": kwargs.get("tags", []),
            }
        except Exception as e:
            logger.error(f"Error creating source info: {e}")
            return False, {"error": f"Error creating source info: {str(e)}"}

    def get_source_details(self, source_id: str) -> tuple[bool, dict[str, Any]]:
        """Retrieve full details including counts."""

        query_s = self.supabase_client.table("archon_sources").select("*").eq("source_id", source_id)
        ok, res = self.execute_query(query_s, "Error getting source details", False)
        if not ok or not res["data"]:
            return False, {"error": f"Source with ID {source_id} not found: {res.get('error', '')}"}

        source_data = res["data"][0]

        query_p = self.supabase_client.table("archon_crawled_pages").select("id").eq("source_id", source_id)
        _, p_res = self.execute_query(query_p, "Error counting pages", False)

        query_c = self.supabase_client.table("archon_code_examples").select("id").eq("source_id", source_id)
        _, c_res = self.execute_query(query_c, "Error counting code examples", False)

        return True, {
            "source": source_data,
            "page_count": len(p_res["data"] or []),
            "code_example_count": len(c_res["data"] or []),
        }

    def list_sources_by_type(self, knowledge_type: str | None = None) -> tuple[bool, dict[str, Any]]:
        """Filtered listing of sources with full metadata parity."""

        query = self.supabase_client.table("archon_sources").select("*")
        if knowledge_type:
            query = query.filter("metadata->>knowledge_type", "eq", knowledge_type)

        success, result = self.execute_query(query, "Error listing sources by type", False)
        if not success:
            return False, {"error": f"Error listing sources by type: {result.get('error')}"}

        sources = []
        for row in result["data"] or []:
            meta = row.get("metadata", {})
            sources.append(
                {
                    "source_id": row["source_id"],
                    "title": row.get("title", ""),
                    "summary": row.get("summary", ""),
                    "knowledge_type": meta.get("knowledge_type", ""),
                    "tags": meta.get("tags", []),
                    "total_word_count": row.get("total_word_count", 0),
                    "created_at": row.get("created_at", ""),
                    "updated_at": row.get("updated_at", ""),
                }
            )
        return True, {"sources": sources, "total_count": len(sources), "knowledge_type_filter": knowledge_type}

    def create_source_from_upload(self, source_id: str, filename: str, **kwargs) -> None:
        """Delegated upload logic."""
        create_source_from_upload_logic(
            self.supabase_client,
            source_id,
            filename,
            kwargs.get("knowledge_type", "technical"),
            kwargs.get("tags", []),
            kwargs.get("chunks_stored", 0),
            kwargs.get("source_url"),
        )
