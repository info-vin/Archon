from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth.dependencies import get_current_user
from ..services.health_service import HealthService

router = APIRouter(tags=["System"])

async def require_system_admin(user=Depends(get_current_user)):
    """
    Dependency to ensure the user has SYSTEM_ADMIN role.
    """
    # Use string comparison as EmployeeRole enum is not yet standardized in backend
    if user.get("role") != "system_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Requires System Administrator privileges."
        )
    return user

@router.get("/health/rag", dependencies=[Depends(require_system_admin)])
async def get_rag_health_check() -> dict[str, Any]:
    """
    Performs a deep integrity check of the RAG system.
    WARNING: This performs DB writes (seeding) and should not be called frequently.
    """
    service = HealthService()
    return await service.check_rag_integrity()

@router.get("/prompts", dependencies=[Depends(require_system_admin)])
async def list_system_prompts() -> list[dict[str, Any]]:
    """
    Lists all system prompts from the database.
    """
    from ..utils import get_supabase_client
    supabase = get_supabase_client()
    response = supabase.table("archon_prompts").select("*").order("prompt_name").execute()
    return response.data or []

@router.post("/prompts/{prompt_name}", dependencies=[Depends(require_system_admin)])
async def update_system_prompt(prompt_name: str, request: dict[str, Any]) -> dict[str, Any]:
    """
    Updates a specific system prompt.
    """
    from ..services.prompt_service import prompt_service
    from ..utils import get_supabase_client

    new_prompt = request.get("prompt")
    description = request.get("description")

    if not new_prompt:
        raise HTTPException(status_code=400, detail="Prompt content is required")

    supabase = get_supabase_client()
    update_data = {"prompt": new_prompt, "updated_at": "now()"}
    if description:
        update_data["description"] = description

    response = supabase.table("archon_prompts").update(update_data).eq("prompt_name", prompt_name).execute()

    if not response.data:
        raise HTTPException(status_code=404, detail=f"Prompt '{prompt_name}' not found")

    # Trigger memory cache reload
    await prompt_service.reload_prompts()

    return response.data[0]
