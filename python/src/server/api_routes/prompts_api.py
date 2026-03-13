"""
Prompts API Hardened - Secure management of AI system instructions.
Standardized RBAC Sealing with correct response unwrapping.
"""


from fastapi import APIRouter, Depends, HTTPException

from src.server.auth.dependencies import get_current_user, requires_permission
from src.server.auth.permissions import USER_MANAGE
from src.server.services.prompt_service import prompt_service

router = APIRouter(prefix="/api/system/prompts", tags=["prompts"])

@router.get("")
async def list_all_prompts(current_user: dict = Depends(get_current_user)):
    """Lists all configured prompts."""
    s, res = await prompt_service.list_prompts()
    if not s:
        raise HTTPException(status_code=500, detail=str(res))
    return res.get("prompts", [])

@router.patch("/{prompt_name}")
async def update_prompt(
    prompt_name: str,
    content: dict[str, str],
    current_user: dict = Depends(requires_permission(USER_MANAGE))
):
    """Updates a system prompt. Requires Admin level permission."""
    new_prompt = content.get("content") or content.get("prompt")
    if not new_prompt:
        raise HTTPException(status_code=422, detail="Prompt content is required")

    try:
        s, res = await prompt_service.update_prompt(prompt_name, new_prompt, description=content.get("description"))
        if not s:
            raise HTTPException(status_code=500, detail=str(res))
        return {"status": "success", "prompt": res}
    except Exception as e:
        if "protected" in str(e).lower():
            raise HTTPException(status_code=403, detail="Cannot modify system protected prompts.") from e
        raise HTTPException(status_code=500, detail=str(e)) from e
