from fastapi import APIRouter, Depends, HTTPException

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.agent_service import AgentService, agent_service

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/agents",
    tags=["agents"],
)


@router.get("/health")
async def agents_health():
    """
    Health check for the AI agents service.
    """
    return {"status": "healthy", "service": "agents"}


@router.get("/assignable", response_model=list[dict])
async def get_assignable_agents(
    current_user: dict = Depends(get_current_user), service: AgentService = Depends(lambda: agent_service)
):
    """
    Get a list of all assignable AI agents.
    Filtered by user role (RBAC).
    """
    try:
        user_role = current_user.get("role", "employee")
        agents = await service.get_assignable_agents(user_role=user_role)
        return agents
    except Exception as e:
        logger.error(f"Failed to get assignable agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assignable agents") from e
