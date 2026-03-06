# python/src/server/services/knowledge/knowledge_item_service.py

from typing import Any

from server.repositories.base_repository import BaseRepository


class KnowledgeItemService(BaseRepository):
    """
    Service for managing knowledge items using the BaseRepository pattern.
    """

    def __init__(self, supabase_client=None):
        super().__init__(supabase_client)

    async def list_items(
        self,
        page: int = 1,
        per_page: int = 20,
        knowledge_type: str | None = None,
        search: str | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """List knowledge items with pagination."""
        def _query():
            query = self.supabase_client.table("archon_knowledge_items").select("*", count="exact")

            if knowledge_type and knowledge_type != "all":
                query = query.eq("knowledge_type", knowledge_type)

            if search:
                query = query.ilike("title", f"%{search}%")

            start = (page - 1) * per_page
            end = start + per_page - 1
            return query.order("created_at", desc=True).range(start, end).execute()

        success, result = self.execute_query(_query, "Failed to list knowledge items")
        if success:
            return True, {
                "items": result["data"],
                "total": result.get("count", 0),
                "page": page,
                "per_page": per_page
            }
        return False, result

    async def get_item(self, source_id: str) -> tuple[bool, dict[str, Any]]:
        """Retrieve a single knowledge item."""
        def _query():
            return self.supabase_client.table("archon_knowledge_items").select("*").eq("id", source_id).single().execute()

        success, result = self.execute_query(_query, f"Failed to get item {source_id}", require_data=True)
        if success:
            return True, {"item": result["data"]}
        return False, result

    async def get_available_sources(self) -> tuple[bool, dict[str, Any]]:
        """Get all available sources for RAG queries."""
        def _query():
            return self.supabase_client.table("archon_knowledge_items").select("id, title, url, knowledge_type").execute()

        success, result = self.execute_query(_query, "Failed to get available sources")
        if success:
            return True, result["data"]
        return False, result
