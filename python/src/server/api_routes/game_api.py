
from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.server.models.auth_models import UserProfileDTO

from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/game", tags=["game"])

class GameSaveRequest(BaseModel):
    save_data: dict[str, Any]

class GameSaveResponse(BaseModel):
    status: str
    message: str

class GameLoadResponse(BaseModel):
    status: str
    message: str | None = None
    save_data: dict[str, Any] | None = None

@router.post("/save", response_model=GameSaveResponse)
async def save_game(request: GameSaveRequest, current_user: UserProfileDTO = Depends(get_current_user)) -> GameSaveResponse:
    user_id = str(current_user.id)
    try:
        from ..services.game_service import GameSaveDataDTO, game_service
        await game_service.save_game(user_id=user_id, save_data=cast(GameSaveDataDTO, request.save_data))
        return GameSaveResponse(status="success", message="Game state saved successfully.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        ) from e

@router.get("/load", response_model=GameLoadResponse)
async def load_game(current_user: UserProfileDTO = Depends(get_current_user)) -> GameLoadResponse:
    user_id = str(current_user.id)
    try:
        from ..services.game_service import game_service
        save_data = await game_service.load_game(user_id=user_id)
        if save_data is None:
            return GameLoadResponse(status="not_found", message="No save game found for this user.", save_data=None)
        return GameLoadResponse(status="success", save_data=cast(dict[str, Any], save_data))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        ) from e
