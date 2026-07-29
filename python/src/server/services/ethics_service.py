from typing import Any, cast

from ..repositories.base_repository import BaseRepository


class EthicsService(BaseRepository):
    def __init__(self):
        super().__init__()

    async def get_ethics_events(self, limit: int = 20) -> list[dict[str, Any]]:
        query = self.supabase_client.table("archon_ethics_events").select("*").order("created_at", desc=True).limit(limit)
        success, res = self.execute_query(query, "Failed to fetch ethics events")
        return cast(list[dict[str, Any]], res.get("data", []) if success else [])

ethics_service = EthicsService()
