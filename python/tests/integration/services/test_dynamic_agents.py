import pytest

from src.server.services.agent_registry import get_agent_config
from src.server.services.agent_service import AgentService


@pytest.mark.asyncio
class TestDynamicAgentsIntegration:
    async def test_dynamic_agent_registry_loading(self):
        """Verify dynamic loading of agent configurations and tools from public.archon_agents."""
        # 1. Test Librarian Config
        config = get_agent_config("librarian")
        assert config is not None
        assert config["name"] == "Archon Librarian"
        assert config["model_tier"] == "lite"
        # Verify tools list loaded from database relation
        assert "rag_search_knowledge_base" in config["tools"]
        assert "perform_web_crawl" in config["tools"]

        # 2. Test DevBot Config
        dev_config = get_agent_config("dev-bot")
        assert dev_config is not None
        assert dev_config["name"] == "Archon DevBot"
        assert dev_config["model_tier"] == "pro"
        assert "apply_modification" in dev_config["tools"]

    async def test_dynamic_assignable_agents_rbac(self):
        """Verify dynamic assignable agents logic using role-agent mappings in database."""
        service = AgentService()

        # 1. Test Sales role
        sales_agents = await service.get_assignable_agents(user_role="sales")
        assert len(sales_agents) == 1
        assert sales_agents[0]["name"] == "MarketBot (Sales)"

        # 2. Test Marketing role
        marketing_agents = await service.get_assignable_agents(user_role="marketing")
        agent_names = {a["name"] for a in marketing_agents}
        assert "MarketBot (Sales)" in agent_names
        assert "Librarian (Knowledge)" in agent_names
        assert len(marketing_agents) == 2
