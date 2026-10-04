from typing import NotRequired, TypedDict, cast

from supabase import Client

from ..repositories.base_repository import BaseRepository


class CreateEthicsEventDTO(TypedDict):
    severity: str
    event_type: str
    description: NotRequired[str | None]
    raw_input: NotRequired[str | None]
    created_at: NotRequired[str]


class ResolveEthicsEventDTO(TypedDict):
    resolved: bool
    resolution_notes: NotRequired[str | None]


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
    def __init__(self, supabase_client: Client | None = None) -> None:
        super().__init__(supabase_client)

    async def get_ethics_events(
        self, limit: int = 20, severity: str | None = None, resolved: bool | None = None
    ) -> list[EthicsEventDTO]:
        query = self.supabase_client.table("archon_ethics_events").select("*")
        if severity is not None:
            query = query.eq("severity", severity)
        if resolved is not None:
            query = query.eq("resolved", resolved)

        query = query.order("created_at", desc=True).limit(limit)
        success, res = await self.execute_query_async(query, "Failed to fetch ethics events")
        return cast(list[EthicsEventDTO], res.get("data", []) if success else [])

    async def get_ethics_event_by_id(self, event_id: str) -> EthicsEventDTO | None:
        query = self.supabase_client.table("archon_ethics_events").select("*").eq("id", event_id)
        success, res = await self.execute_query_async(query, f"Failed to fetch ethics event {event_id}")
        if not success or not res.get("data"):
            return None
        return cast(EthicsEventDTO, res["data"][0])

    async def create_ethics_event(self, event_data: CreateEthicsEventDTO) -> EthicsEventDTO | None:
        query = self.supabase_client.table("archon_ethics_events").insert(event_data)
        success, res = await self.execute_query_async(query, "Failed to create ethics event", require_data=True)
        if not success or not res.get("data"):
            return None
        return cast(EthicsEventDTO, res["data"][0])

    async def resolve_ethics_event(self, event_id: str, resolution_notes: str | None = None) -> EthicsEventDTO | None:
        payload: ResolveEthicsEventDTO = {
            "resolved": True,
            "resolution_notes": resolution_notes,
        }
        query = self.supabase_client.table("archon_ethics_events").update(payload).eq("id", event_id)
        success, res = await self.execute_query_async(query, f"Failed to resolve ethics event {event_id}", require_data=True)
        if not success or not res.get("data"):
            return None
        return cast(EthicsEventDTO, res["data"][0])


ethics_service = EthicsService()
