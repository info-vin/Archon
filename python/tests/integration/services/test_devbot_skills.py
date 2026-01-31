import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.services.agent_service import AgentService


@pytest.fixture
def mock_mcp_client():
    client = AsyncMock()
    # Mock tool response
    client.search_code_examples.return_value = "Found example: from foo.bar import Baz"
    return client

@pytest.mark.asyncio
async def test_analyze_error_with_skills_flow(mock_mcp_client):
    """
    Test the 'Look-Before-Leap' flow where DevBot uses a tool before fixing.
    """
    # 1. Setup Service with MCP
    service = AgentService(mcp_client=mock_mcp_client)

    # 2. Mock LLM Responses
    # We need two responses:
    # Round 1: Tool Call (Search)
    # Round 2: Final JSON (Fix)

    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "search_code_examples"
    mock_tool_call.function.arguments = '{"query": "ImportError"}'
    mock_tool_call.id = "call_123"

    # Response 1: Wants to use tool
    r1_message = MagicMock()
    r1_message.tool_calls = [mock_tool_call]
    r1_message.content = None
    r1_choice = MagicMock()
    r1_choice.message = r1_message

    # Response 2: Final verdict (after seeing tool output)
    final_fix = {
        "file_path": "script.py",
        "fixed_content": "import foo",
        "reasoning": "Fixed based on search"
    }
    r2_message = MagicMock()
    r2_message.tool_calls = None
    r2_message.content = json.dumps(final_fix)
    r2_choice = MagicMock()
    r2_choice.message = r2_message

    # Mock the LLM client
    mock_llm_client = AsyncMock()
    # side_effect for consecutive calls
    mock_llm_client.chat.completions.create.side_effect = [
        MagicMock(choices=[r1_choice]), # Round 1
        MagicMock(choices=[r2_choice])  # Round 2
    ]

    # Context Manager Mock
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_llm_client

    # Define a mock provider config with a specific model
    mock_provider_config = {"chat_model": "test-model-v1"}

    with patch("server.services.agent_service.get_llm_client", return_value=mock_ctx), \
         patch("server.services.agent_service.credential_service.get_active_provider", return_value=mock_provider_config):

        # 3. Execute
        result = await service._analyze_error_with_structured_output(
            command="python script.py",
            stderr="ImportError: No module named foo"
        )

        # 4. Assertions

        # Verify Tool Execution
        mock_mcp_client.search_code_examples.assert_called_once_with(query="ImportError")

        # Verify LLM was called twice
        assert mock_llm_client.chat.completions.create.call_count == 2

        # Verify that the model passed to create() matches the provider config
        # (This ensures we aren't hardcoding gpt-4o in the service logic)
        args, kwargs = mock_llm_client.chat.completions.create.call_args_list[0]
        assert kwargs["model"] == "test-model-v1"

        # Verify Round 2 included the tool output
        # Get arguments of the second call
        call_args = mock_llm_client.chat.completions.create.call_args_list[1]
        messages = call_args.kwargs['messages']

        # Check if history contains the tool output
        assert len(messages) >= 3 # User prompt + Assistant Tool Request + Tool Output
        assert messages[-1]["role"] == "tool"
        assert "Found example" in messages[-1]["content"]

        # Verify Final Result
        assert result == final_fix

@pytest.mark.asyncio
async def test_analyze_error_graceful_degradation():
    """
    Test that DevBot works even if MCP client is missing (legacy mode).
    """
    # 1. Setup Service WITHOUT MCP
    service = AgentService(mcp_client=None)

    # Response: Direct Fix (No tools available)
    final_fix = {"file_path": "a.py", "fixed_content": "print('ok')", "reasoning": "guess"}
    r1_message = MagicMock()
    r1_message.tool_calls = None
    r1_message.content = json.dumps(final_fix)

    mock_llm_client = AsyncMock()
    mock_llm_client.chat.completions.create.return_value = MagicMock(choices=[MagicMock(message=r1_message)])

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_llm_client

    with patch("server.services.agent_service.get_llm_client", return_value=mock_ctx), \
         patch("server.services.agent_service.credential_service.get_active_provider", return_value={"chat_model": "test-model-v1"}):

        result = await service._analyze_error_with_structured_output("cmd", "err")

        assert result == final_fix
        # Tools should be None in the call
        call_args = mock_llm_client.chat.completions.create.call_args
        assert call_args.kwargs['tools'] is None
