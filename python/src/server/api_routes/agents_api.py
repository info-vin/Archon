from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict

from ..config.logfire_config import logfire
from ..services.agent_service import agent_service, AgentService

router = APIRouter(
    prefix="/api/agents",
    tags=["agents"],
)

@router.get("/assignable", response_model=List[Dict])
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
