# python/src/server/services/agent_service.py

import asyncio

from ..config.logfire_config import get_logger
from .shared_constants import AI_AGENT_ROLES # Import AI_AGENT_ROLES from new shared module

class AgentService:
    """Service for handling business logic related to AI agents."""

    async def get_assignable_agents(self) -> list[dict]:
        """
        Retrieves a list of assignable AI agents.
        """
        assignable_agents = []
        for role_name, agent_id in AI_AGENT_ROLES.items():
            assignable_agents.append({"id": agent_id, "name": role_name, "role": role_name})
        return assignable_agents

    async def run_agent_task(self, task_id: str, agent_id: str):
        """
        Placeholder method to run a task by an AI agent.
        This updates the task status to 'processing' and then simulates work.
        """
        # Local import to break circular dependency
        from ..services.projects.task_service import task_service

        logger = get_logger(__name__)
        logger.info(f"AI agent '{agent_id}' has been notified to start working on task '{task_id}'.")

        # --- NEW LOGIC: Update task status to processing ---
        # Call task_service to update the task status. This provides immediate feedback in the UI.
        success, result = await task_service.update_task(
            task_id, {"status": "processing", "assignee": agent_id} # Explicitly set assignee to ensure consistency
        )
        if success:
            logger.info(f"Task '{task_id}' status updated to 'processing' by agent '{agent_id}'.")
        else:
            logger.error(f"Failed to update task '{task_id}' status to 'processing': {result.get('error')}")
        # --- END NEW LOGIC ---

        # Simulate some async work (keeping original placeholder for now)
        await asyncio.sleep(1)
        logger.info(f"AI agent '{agent_id}' finished its work for task '{task_id}'.")

# Create a singleton instance of the service
agent_service = AgentService()