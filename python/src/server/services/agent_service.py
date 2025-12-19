# python/src/server/services/agent_service.py

# Known AI agent roles that can be assigned tasks
AI_AGENT_ROLES = {
    "Market Researcher": "ai-researcher-1",
    "Internal Knowledge Expert": "ai-knowledge-expert-1"
}

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
        A placeholder method to simulate running a task by an AI agent.
        This will be called when a task is assigned to an AI.
        """
        # In a real implementation, this would trigger a process,
        # call an external API, or add a job to a dedicated agent queue.
        # For now, we just log the action.
        import asyncio

        from ..config.logfire_config import get_logger
        logger = get_logger(__name__)
        logger.info(f"AI agent '{agent_id}' has been notified to start working on task '{task_id}'.")
        # Simulate some async work
        await asyncio.sleep(1)
        logger.info(f"AI agent '{agent_id}' finished its work for task '{task_id}'.")

# Create a singleton instance of the service
agent_service = AgentService()
