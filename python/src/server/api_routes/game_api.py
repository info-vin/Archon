from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Any

from ..auth.dependencies import get_current_user
from ..utils import get_supabase_client

router = APIRouter(prefix="/game", tags=["game"])

class GameSaveRequest(BaseModel):
    save_data: dict[str, Any]

@router.post("/save")
async def save_game(request: GameSaveRequest, current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("id"))
    supabase = get_supabase_client()
    
    # Perform upsert to supabase
    try:
        res = supabase.table("user_game_saves").upsert({
            "user_id": user_id,
            "save_data": request.save_data,
            "updated_at": "now()"
        }).execute()
        
        if not res.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save game state."
            )
            
        return {"status": "success", "message": "Game state saved successfully."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )

@router.get("/load")
async def load_game(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user.get("id"))
    supabase = get_supabase_client()
    
    try:
        res = supabase.table("user_game_saves").select("save_data").eq("user_id", user_id).execute()
        
        if not res.data:
            return {"status": "not_found", "message": "No save game found for this user.", "save_data": None}
            
        return {"status": "success", "save_data": res.data[0]["save_data"]}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
