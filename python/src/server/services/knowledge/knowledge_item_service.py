# python/src/server/services/knowledge/knowledge_item_service.py

from typing import Any

from src.server.repositories.base_repository import BaseRepository


class KnowledgeItemService(BaseRepository):
    """
    Service for managing knowledge items using the BaseRepository pattern.
    """

    def __init__(self, supabase_client: Any = None) -> None:
        super().__init__(supabase_client)

    async def list_items(
        self, page: int = 1, per_page: int = 20, knowledge_type: str | None = None, search: str | None = None
    ) -> tuple[bool, dict[str, Any]]:
        """List knowledge items with pagination."""

        query = self.supabase_client.table("archon_sources").select("*", count="exact")  # 合法

        if knowledge_type and knowledge_type != "all":
            # knowledge_type is stored in metadata JSONB
            query = query.contains("metadata", {"knowledge_type": knowledge_type})

        if search:
            # search in title or metadata->description
            query = query.or_(f"title.ilike.%{search}%,summary.ilike.%{search}%")

        start = (page - 1) * per_page
        end = start + per_page - 1
        query = query.order("created_at", desc=True).range(start, end)

        success, result = self.execute_query(query, "Failed to list knowledge items", require_data=False)
        if success:
            data = result.get("data", [])
            return True, {
                "items": data,
                "total": result.get("count", 0) or len(data),
                "page": page,
                "per_page": per_page,
            }
        return False, result

    async def get_item(self, source_id: str) -> tuple[bool, dict[str, Any]]:
        """Retrieve a single knowledge item."""

        query = self.supabase_client.table("archon_sources").select("*").eq("source_id", source_id)  # 合法
        success, result = self.execute_query(query, f"Failed to get item {source_id}", require_data=True)
        if success:
            data = result.get("data", [])
            item_data = data[0] if isinstance(data, list) and data else (data if data else {})
            return True, {"item": item_data}
        return False, result

    async def update_item(self, source_id: str, updates: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        """
        Update a knowledge item's metadata.
        """
        try:
            # Prepare update data
            update_data = {}

            # Handle title updates
            if "title" in updates:
                update_data["title"] = updates["title"]

            # Handle metadata updates
            metadata_fields = [
                "description",
                "knowledge_type",
                "tags",
                "status",
                "update_frequency",
                "group_name",
            ]
            metadata_updates = {k: v for k, v in updates.items() if k in metadata_fields}

            if metadata_updates:
                # Get current metadata
                meta_query = (
                    self.supabase_client.table("archon_sources")  # 合法
                    .select("metadata")
                    .eq("source_id", source_id)
                )
                meta_success, meta_res = self.execute_query(meta_query, "Error getting metadata", require_data=False)

                current_metadata = {}
                if meta_success and meta_res.get("data"):
                    current_metadata = meta_res["data"][0].get("metadata", {})

                current_metadata.update(metadata_updates)
                update_data["metadata"] = current_metadata

            # Perform the update
            update_query = (
                self.supabase_client.table("archon_sources")  # 合法
                .update(update_data)
                .eq("source_id", source_id)
            )
            success, result = self.execute_query(update_query, f"Failed to update item {source_id}", require_data=True)
            if success:
                return True, {"message": f"Successfully updated knowledge item {source_id}", "source_id": source_id}
            return False, result

        except Exception as e:
            return False, {"error": str(e)}

    async def get_available_sources(self) -> tuple[bool, dict[str, Any]]:
        """Get all available sources for RAG queries."""

        query = self.supabase_client.table("archon_sources").select("source_id, title, metadata")  # 合法
        success, result = self.execute_query(query, "Failed to get available sources")
        if success:
            # Reformat to match frontend expectation (backward compatibility)
            formatted = []
            for row in result["data"]:
                meta = row.get("metadata", {})
                formatted.append(
                    {
                        "id": row["source_id"],
                        "source_id": row["source_id"],
                        "title": row["title"],
                        "knowledge_type": meta.get("knowledge_type", "technical"),
                        "url": row.get("source_url") or meta.get("original_url", f"source://{row['source_id']}"),
                    }
                )
            return True, {"sources": formatted}
        return False, result
