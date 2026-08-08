from typing import NotRequired, TypedDict, cast

from ..repositories.base_repository import BaseRepository


class EthicsEventDTO(TypedDict):
    id: NotRequired[str]
    severity: str
    event_type: str
    description: NotRequired[str | None]
    raw_input: NotRequired[str | None]
    created_at: NotRequired[str]
    resolved: NotRequired[bool]
    resolution_notes: NotRequired[str | None]


class EthicsService(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    async def get_ethics_events(self, limit: int = 20) -> list[EthicsEventDTO]:
        query = self.supabase_client.table("archon_ethics_events").select("*").order("created_at", desc=True).limit(limit) # 合法
        success, res = self.execute_query(query, "Failed to fetch ethics events")
        return cast(list[EthicsEventDTO], res.get("data", []) if success else [])

ethics_service = EthicsService()
