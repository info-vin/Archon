
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.prompt_service import prompt_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/system/prompts", tags=["system"])

class UpdatePromptRequest(BaseModel):
    content: str
    description: str | None = None

@router.get("")
async def list_prompts(current_user: dict = Depends(get_current_user)):
    """
    List all system prompts. Restricted to Admins.
    """
    role = current_user.get("role", "viewer").lower()
    if role not in ["system_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    prompts = await prompt_service.list_prompts()
    return prompts

@router.patch("/{prompt_name}")
async def update_prompt(
    prompt_name: str,
    request: UpdatePromptRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a system prompt. Restricted to Admins.
    """
    role = current_user.get("role", "viewer").lower()
    if role not in ["system_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions.")

    success, message = await prompt_service.update_prompt(
        prompt_name=prompt_name,
        content=request.content,
        description=request.description
    )

    if not success:
        raise HTTPException(status_code=500, detail=message)

    return {"success": True, "message": message}
