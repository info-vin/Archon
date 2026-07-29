from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.server.models.auth_models import UserProfileDTO

from ..auth.dependencies import get_current_user

router = APIRouter(prefix="/game", tags=["game"])

class GameSaveRequest(BaseModel):
    save_data: dict[str, Any]

@router.post("/save")
async def save_game(request: GameSaveRequest, current_user: UserProfileDTO = Depends(get_current_user)):
    user_id = str(current_user.id)
    try:
        from ..services.game_service import game_service
        await game_service.save_game(user_id=user_id, save_data=request.save_data)
        return {"status": "success", "message": "Game state saved successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        ) from e

@router.get("/load")
async def load_game(current_user: UserProfileDTO = Depends(get_current_user)):
    user_id = str(current_user.id)
    try:
        from ..services.game_service import game_service
        save_data = await game_service.load_game(user_id=user_id)
        if save_data is None:
            return {"status": "not_found", "message": "No save game found for this user.", "save_data": None}
        return {"status": "success", "save_data": save_data}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        ) from e
