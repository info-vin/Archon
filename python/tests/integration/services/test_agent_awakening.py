
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.agent_registry import get_agent_config
from src.server.services.agent_service import AgentService


@pytest.mark.asyncio
class TestAgentAwakening:

    async def test_agent_registry_load(self):
        """Verify Registry loads correct config for known agents."""
        # 1. MarketBot
        market_config = get_agent_config("ai-market-bot")
        assert market_config is not None
        assert market_config["name"] == "Archon MarketBot"
        assert "search_job_market" in market_config["tools"]
        assert "Marketing Content Writer" in market_config["system_prompt"] or "Blog" in market_config["system_prompt"]

        # 2. Librarian
        lib_config = get_agent_config("ai-librarian")
        assert lib_config is not None
        assert lib_config["name"] == "Archon Librarian"
        assert "rag_search_knowledge_base" in lib_config["tools"]

    @patch("src.server.services.agent_service.get_llm_client")
    # Patch the singleton instance directly where it lives
    @patch("src.server.services.projects.task_service.task_service")
    async def test_marketbot_awakening_loop(self, mock_task_service, mock_get_client):
        """
        Verify MarketBot wakes up, loads its prompt, and executes a task loop.
        """
        # Physical Alignment: Setup Mock MCP Client with new OpenAI-style tool schema (Phase 4.6.19)
        mock_mcp = AsyncMock()
        mock_mcp.list_tools.return_value = [
            {"type": "function", "function": {"name": "search_job_market", "description": "Search 104", "parameters": {}}},
            {"type": "function", "function": {"name": "perform_rag_query", "description": "Search RAG", "parameters": {}}}
        ]
        service = AgentService(mcp_client=mock_mcp)

        # Mock Task Service (Async methods must return awaitables)
        mock_task_service.get_task = AsyncMock(return_value=(True, {"task": {"title": "Write a blog", "description": "About AI"}}))
        mock_task_service.update_task = AsyncMock(return_value=(True, {}))

        # Mock LLM Client
        mock_client_instance = AsyncMock()
        mock_get_client.return_value.__aenter__.return_value = mock_client_instance

        # Simulate LLM Response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Blog Draft Content"
        mock_response.choices[0].message.tool_calls = None
        mock_client_instance.chat.completions.create.return_value = mock_response

        # Execute Run (MarketBot)
        await service.run_agent_task(task_id="task_123", agent_id="ai-market-bot")

        # Verify:
        # 1. Task was fetched
        mock_task_service.get_task.assert_called_with("task_123")

        # 2. LLM was called with MarketBot's System Prompt
        call_args = mock_client_instance.chat.completions.create.call_args
        assert call_args is not None
        messages = call_args.kwargs["messages"]
        system_msg = messages[0]
        assert system_msg["role"] == "system"
        # Check if system prompt matches registry
        config = get_agent_config("ai-market-bot")
        assert system_msg["content"] == config["system_prompt"]

        # 3. Tools were passed
        tools = call_args.kwargs["tools"]
        assert tools is not None
        # We expected filtered tools for MarketBot
        tool_names = [t["function"]["name"] for t in tools]
        assert "search_job_market" in tool_names
        assert "search_code_examples" not in tool_names # DevBot tool should NOT be here
