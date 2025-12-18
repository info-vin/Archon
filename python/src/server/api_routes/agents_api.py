from fastapi import APIRouter, Depends
from typing import List, Dict

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
    agents = await service.get_assignable_agents()
    return agents
