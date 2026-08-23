from typing import TypedDict, cast

from ..repositories.base_repository import BaseRepository


class GameSaveDataDTO(TypedDict, total=False):
    funds: int
    reputation: int
    # Add other flexible game state fields as needed...

class GameSaveResultDTO(TypedDict):
    id: str
    user_id: str
    save_data: GameSaveDataDTO
    updated_at: str

class GameService(BaseRepository):
    def __init__(self) -> None:
        super().__init__()

    async def save_game(self, user_id: str, save_data: GameSaveDataDTO) -> GameSaveResultDTO:
        query = self.supabase_client.table("user_game_saves").upsert({ # 合法
            "user_id": user_id,
            "save_data": save_data,
            "updated_at": "now()"
        })
        success, res = self.execute_query(query, "Failed to save game state", require_data=True)
        if not success:
            raise ValueError("Failed to save game state.")
        return cast(GameSaveResultDTO, res.get("data", [{}])[0])

    async def load_game(self, user_id: str) -> GameSaveDataDTO | None:
        query = self.supabase_client.table("user_game_saves").select("save_data").eq("user_id", user_id) # 合法
        success, res = self.execute_query(query, "Failed to load game state")
        if not success:
            raise ValueError("Failed to load game state.")

        data = res.get("data", [])
        if not data:
            return None

        return cast(GameSaveDataDTO, data[0].get("save_data"))

game_service = GameService()
