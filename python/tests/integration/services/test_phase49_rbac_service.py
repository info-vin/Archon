

import pytest

from src.server.services.agent_service import AgentService


@pytest.mark.asyncio
class TestPhase49RBAC:

    async def test_sales_role_restrictions(self):
        """Alice (Sales) should ONLY see MarketBot."""
        service = AgentService()

        # Test Sales Role
        agents = await service.get_assignable_agents(user_role="sales")

        agent_names = [a["name"] for a in agents]
        # Check substrings because names are like "MarketBot (Sales)"
        assert any("MarketBot" in name for name in agent_names)
        assert not any("Librarian" in name for name in agent_names)
        assert not any("DevBot" in name for name in agent_names)

        # Verify Enrichment (Phase 4.12)
        market_bot = next(a for a in agents if "MarketBot" in a["name"])
        assert "tools" in market_bot
        assert "description" in market_bot
        assert len(market_bot["tools"]) > 0

        assert len(agents) == 1

    async def test_marketing_role_restrictions(self):
        """Bob (Marketing) should see MarketBot + Librarian."""
        service = AgentService()

        agents = await service.get_assignable_agents(user_role="marketing")

        agent_names = [a["name"] for a in agents]
        assert any("MarketBot" in name for name in agent_names)
        assert any("Librarian" in name for name in agent_names)
        assert not any("DevBot" in name for name in agent_names)
        assert len(agents) == 2

    async def test_manager_role_access(self):
        """Charlie (Manager) should see ALL agents."""
        service = AgentService()

        agents = await service.get_assignable_agents(user_role="manager")

        agent_names = [a["name"] for a in agents]
        assert any("MarketBot" in name for name in agent_names)
        assert any("Librarian" in name for name in agent_names)
        assert not any("POBot" in name for name in agent_names)  # System bot, not manually assignable
        assert any("DevBot" in name for name in agent_names)
        # Ensure at least 3 agent roles exist (MarketBot, Librarian, DevBot)
        assert len(agents) >= 3
