from typing import NotRequired, TypedDict, cast

from supabase import Client

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


class CreateEthicsEventDTO(TypedDict):
    severity: str
    event_type: str
    description: NotRequired[str | None]
    raw_input: NotRequired[str | None]
    resolved: NotRequired[bool]
    resolution_notes: NotRequired[str | None]


class ResolveEthicsEventDTO(TypedDict):
    resolved: bool
    resolution_notes: NotRequired[str | None]


class EthicsService(BaseRepository):
    def __init__(self, supabase_client: Client | None = None) -> None:
        super().__init__(supabase_client)

    async def get_ethics_events(self, limit: int = 20) -> list[EthicsEventDTO]:
        query = self.supabase_client.table("archon_ethics_events").select("*").order("created_at", desc=True).limit(limit)
        success, res = await self.execute_query_async(query, "Failed to fetch ethics events")
        return cast(list[EthicsEventDTO], res.get("data", []) if success else [])

    async def create_ethics_event(self, event_data: CreateEthicsEventDTO) -> EthicsEventDTO | None:
        query = self.supabase_client.table("archon_ethics_events").insert(event_data)
        success, res = await self.execute_query_async(query, "Failed to create ethics event", require_data=True)
        if not success or not res.get("data"):
            return None
        data = res.get("data", [])
        return cast(EthicsEventDTO, data[0] if isinstance(data, list) and data else None)

    async def resolve_ethics_event(self, event_id: str, resolution_notes: str | None = None) -> EthicsEventDTO | None:
        update_payload: ResolveEthicsEventDTO = {
            "resolved": True,
        }
        if resolution_notes is not None:
            update_payload["resolution_notes"] = resolution_notes

        query = (
            self.supabase_client.table("archon_ethics_events")
            .update(update_payload)
            .eq("id", event_id)
        )
        success, res = await self.execute_query_async(query, f"Failed to resolve ethics event {event_id}", require_data=True)
        if not success or not res.get("data"):
            return None
        data = res.get("data", [])
        return cast(EthicsEventDTO, data[0] if isinstance(data, list) and data else None)


ethics_service = EthicsService()
