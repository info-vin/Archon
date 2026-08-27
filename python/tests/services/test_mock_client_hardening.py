import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.server.services.llm.clients import get_llm_client
from src.server.services.agents.dispatcher import DefaultLLMStrategy
from src.server.services.llm.base import MockMessage
from src.server.config.config import EnvironmentConfig


@pytest.mark.asyncio
async def test_get_llm_client_fail_fast_in_non_testing():
    """Verify that in non-testing mode, if the API key is missing, get_llm_client raises ValueError."""
    mock_config = MagicMock(spec=EnvironmentConfig)
    mock_config.is_testing = False
    
    with patch("src.server.config.config.get_config", return_value=mock_config), \
         patch("src.server.services.credentials.provider_configs._get_provider_api_key", AsyncMock(return_value=None)):
        # We call get_llm_client for google with no api_key
        try:
            async with get_llm_client(provider="google", api_key=None) as client:
                pass
            pytest.fail("Should have raised ValueError on missing API key in non-testing environment")
        except ValueError as e:
            assert "CRITICAL: Google API key not found" in str(e)


@pytest.mark.asyncio
async def test_get_llm_client_allows_mock_in_testing():
    """Verify that in testing mode, if the API key is missing, get_llm_client falls back to MockLLMClient."""
    mock_config = MagicMock(spec=EnvironmentConfig)
    mock_config.is_testing = True
    
    with patch("src.server.config.config.get_config", return_value=mock_config), \
         patch("src.server.services.credentials.provider_configs._get_provider_api_key", AsyncMock(return_value=None)):
        async with get_llm_client(provider="google", api_key=None) as client:
            from src.server.services.llm.base import MockLLMClient
            assert isinstance(client, MockLLMClient)


@pytest.mark.asyncio
async def test_dispatcher_safely_handles_mock_message():
    """Verify that DefaultLLMStrategy does not crash with AttributeError when handling MockMessage."""
    # We mock get_llm_client to yield a client that returns a MockMessage (which lacks tool_calls)
    mock_message = MockMessage(content="Hello Mock World")
    
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    
    mock_completions = AsyncMock()
    mock_completions.create.return_value = mock_response
    
    mock_chat = MagicMock()
    mock_chat.completions = mock_completions
    
    mock_client = MagicMock()
    mock_client.chat = mock_chat
    
    # Create mock task data and agent config
    task_id = "test-task-123"
    task_data = {
        "title": "Test Task",
        "description": "Test Details",
        "status": "todo"
    }
    agent_id = "test-agent-456"
    
    # Mock task_service and agent_service
    mock_task_service = AsyncMock()
    mock_agent_service = MagicMock()
    # List tools must be an AsyncMock to be awaitable
    mock_agent_service.mcp_client = MagicMock()
    mock_agent_service.mcp_client.list_tools = AsyncMock(return_value=[])
    
    agent_config = {
        "system_prompt": "You are a helpful assistant.",
        "model_tier": "lite",
        "tools": []
    }
    
    with patch("src.server.services.agents.dispatcher.get_agent_config", return_value=agent_config), \
         patch("src.server.services.agents.dispatcher.get_llm_client") as mock_client_ctx, \
         patch("src.server.services.agents.dispatcher.task_service", mock_task_service), \
         patch("src.server.services.agents.dispatcher.GlobalThrottler.wait_for_capacity", AsyncMock()):
        
        # Make the context manager yield our mock_client
        mock_client_ctx.return_value.__aenter__.return_value = mock_client
        
        strategy = DefaultLLMStrategy()
        # Execute the strategy
        await strategy.execute(task_id, task_data, agent_id, mock_agent_service)
        
        # Verify task was updated to done and output saved
        mock_task_service.update_task.assert_any_call(task_id, {"status": "done"})
        mock_task_service.save_agent_output.assert_called_once()
        saved_payload = mock_task_service.save_agent_output.call_args[0][1]
        assert saved_payload["content"] == "Hello Mock World"
