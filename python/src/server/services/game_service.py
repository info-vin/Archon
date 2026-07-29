from typing import Any, cast

from ..repositories.base_repository import BaseRepository


class GameService(BaseRepository):
    def __init__(self):
        super().__init__()

    async def save_game(self, user_id: str, save_data: dict[str, Any]) -> dict[str, Any]:
        query = self.supabase_client.table("user_game_saves").upsert({
            "user_id": user_id,
            "save_data": save_data,
            "updated_at": "now()"
        })
        success, res = self.execute_query(query, "Failed to save game state", require_data=True)
        if not success:
            raise ValueError("Failed to save game state.")
        return cast(dict[str, Any], res.get("data", [{}])[0])

    async def load_game(self, user_id: str) -> dict[str, Any] | None:
        query = self.supabase_client.table("user_game_saves").select("save_data").eq("user_id", user_id)
        success, res = self.execute_query(query, "Failed to load game state")
        if not success:
            raise ValueError("Failed to load game state.")

        data = res.get("data", [])
        if not data:
            return None

        return cast(dict[str, Any], data[0].get("save_data"))

game_service = GameService()
