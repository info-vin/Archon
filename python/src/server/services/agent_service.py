# python/src/server/services/agent_service.py

class AgentService:
    """Service for handling business logic related to AI agents."""

    async def get_assignable_agents(self) -> list[dict]:
        """
        Retrieves a list of assignable AI agents.

        This is a placeholder implementation.
        """
        # In the future, this could fetch agents from a database
        # or a configuration file.
        return [
            {"id": "ai-researcher-1", "name": "AI Market Researcher", "role": "Market Researcher"},
            {"id": "ai-knowledge-expert-1", "name": "AI Internal Knowledge Expert", "role": "Internal Knowledge Expert"},
        ]

# Create a singleton instance of the service
agent_service = AgentService()
