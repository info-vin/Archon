
from fastapi import APIRouter, Depends, HTTPException

from ..config.logfire_config import logfire
from ..services.agent_service import AgentService, agent_service

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
    service: AgentService = Depends(lambda: agent_service)
):
    """
    Get a list of all assignable AI agents.
    """
    try:
        agents = await service.get_assignable_agents()
        return agents
    except Exception as e:
        logfire.error(f"Failed to get assignable agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assignable agents") from e
