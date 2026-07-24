import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.agents.dispatcher import DefaultLLMStrategy


@pytest.mark.asyncio
async def test_default_llm_strategy_timeout():
    """
    Phase 5.9.14: Verify that DefaultLLMStrategy raises a TimeoutError
    when the LLM SDK call hangs, instead of deadlocking the worker.
    """
    strategy = DefaultLLMStrategy()

    # Create dummy dependencies
    mock_agent_service = MagicMock()
    mock_agent_service.mcp_client = None

    task_data = {"title": "Test Timeout", "description": "Verify timeout"}

    # Mock get_agent_config to bypass config check
    with patch("src.server.services.agents.dispatcher.get_agent_config") as mock_get_config, \
         patch("src.server.services.agents.dispatcher.get_llm_client") as mock_get_client, \
         patch("src.server.services.agents.dispatcher.credential_service") as mock_cred_service, \
         patch("src.server.services.agents.dispatcher.GlobalThrottler"), \
         patch("src.server.services.agents.dispatcher.task_service") as mock_task_service:

        mock_get_config.return_value = {"system_prompt": "You are a test bot", "tools": [], "model_tier": "lite"}
        mock_cred_service.get_credential = AsyncMock(return_value="fake_key")
        mock_task_service.update_task = AsyncMock()

        # Mock the LLM client to hang indefinitely (or longer than timeout)
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create = MagicMock()

        async def slow_create(*args, **kwargs):
            await asyncio.sleep(2.0)  # We'll mock the wait_for timeout to be smaller
            return MagicMock()

        mock_client_instance.chat.completions.create = slow_create

        # Mock the async context manager for get_llm_client
        class AsyncContextManagerMock:
            async def __aenter__(self):
                return mock_client_instance
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

        mock_get_client.return_value = AsyncContextManagerMock()

        # Patch asyncio.wait_for to have a tiny timeout just for this test
        original_wait_for = asyncio.wait_for
        async def mock_wait_for(coro, timeout):
            return await original_wait_for(coro, timeout=0.1)

        with patch("src.server.services.agents.dispatcher.asyncio.wait_for", new=mock_wait_for):
            # This should catch the TimeoutError inside the strategy and log it,
            # then set the task status to failed, instead of throwing an unhandled exception.
            await strategy.execute(
                task_id="test_task_123",
                task_data=task_data,
                agent_id="test_agent",
                agent_service=mock_agent_service
            )

        # Verify that task_service.update_task was called with status=failed
        mock_task_service.update_task.assert_called_with("test_task_123", {"status": "failed"})
