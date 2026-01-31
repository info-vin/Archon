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
    [Phase 4.7] Test the 'Look-Before-Leap' flow where DevBot uses a tool before fixing.
    """
    # 1. Setup Service with MCP
    service = AgentService(mcp_client=mock_mcp_client)
    
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
    mock_llm_client.chat.completions.create.side_effect = [
        MagicMock(choices=[r1_choice]), # Round 1
        MagicMock(choices=[r2_choice])  # Round 2
    ]
    
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_llm_client
    
    mock_provider_config = {"chat_model": "test-model-v1"}
    
    with patch("server.services.agent_service.get_llm_client", return_value=mock_ctx), \
         patch("server.services.agent_service.credential_service.get_active_provider", return_value=mock_provider_config):
        
        result = await service._analyze_error_with_structured_output(
            command="python script.py", 
            stderr="ImportError: No module named foo"
        )
        
        mock_mcp_client.search_code_examples.assert_called_once_with(query="ImportError")
        assert mock_llm_client.chat.completions.create.call_count == 2
        assert result == final_fix

@pytest.mark.asyncio
async def test_analyze_error_graceful_degradation():
    """
    [Phase 4.7] Test that DevBot works even if MCP client is missing (legacy mode).
    """
    service = AgentService(mcp_client=None)
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
        call_args = mock_llm_client.chat.completions.create.call_args
        assert call_args.kwargs['tools'] is None
