from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.server.services.agents.dispatcher
from src.server.services.agent_service import AgentService
from src.server.services.projects.task_service import task_service as real_task_service


@pytest.mark.asyncio
async def test_agent_service_dynamic_tool_discovery():
    """
    Phase 4.6.19: Verify that AgentService dynamically fetches tools from MCPClient
    instead of using hardcoded lists.
    """
    # 1. Setup Mock MCP Client with a dynamic tool list
    mock_mcp_client = MagicMock()
    mock_mcp_client.list_tools = AsyncMock(
        return_value=[
            {
                "type": "function",
                "function": {
                    "name": "dynamic_test_tool",
                    "description": "A dynamically discovered tool",
                    "parameters": {"type": "object", "properties": {"arg": {"type": "string"}}},
                },
            }
        ]
    )

    # 2. Setup Mock Agent Registry config
    mock_config = {"name": "Test Bot", "system_prompt": "You are a test bot.", "tools": ["dynamic_test_tool"]}

    # 3. Setup AgentService with the mock client
    service = AgentService(mcp_client=mock_mcp_client)

    # 4. Mock dependencies
    with (
        patch.object(src.server.services.agents.dispatcher, "get_agent_config", return_value=mock_config),
        patch.object(real_task_service, "get_task", new_callable=AsyncMock, return_value=(True, {"task": {"id": "t1", "title": "Test Task"}})),
        patch.object(real_task_service, "update_task", new_callable=AsyncMock, return_value=(True, {})),
        patch.object(real_task_service, "save_agent_output", new_callable=AsyncMock, return_value=(True, {})),
        patch.object(src.server.services.agents.dispatcher, "get_llm_client") as mock_get_llm,
        patch.object(src.server.services.agents.dispatcher, "credential_service") as mock_cred_svc,
    ):
        mock_cred_svc.get_credential = AsyncMock(return_value="fake_key")
        # Mock LLM response
        mock_client_ctx = AsyncMock()
        mock_get_llm.return_value.__aenter__.return_value = mock_client_ctx

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Task Completed"
        mock_response.choices[0].message.tool_calls = None
        mock_client_ctx.chat.completions.create = AsyncMock(return_value=mock_response)

        # 5. Execute the general agent task
        await service._run_general_agent_task("t1", "ai-test-bot")

        # 6. PHYSICAL ASSERTIONS
        # Verify MCPClient.list_tools was called
        mock_mcp_client.list_tools.assert_called_once()

        # Verify the tools passed to LLM match the dynamic tool from MCP
        args, kwargs = mock_client_ctx.chat.completions.create.call_args
        passed_tools = kwargs.get("tools")

        assert passed_tools is not None, "Tools should have been passed to LLM"
        assert len(passed_tools) == 1
        assert passed_tools[0]["function"]["name"] == "dynamic_test_tool"
        assert "Search 104" not in str(passed_tools), "Hardcoded tools should NOT be present"


@pytest.mark.asyncio
async def test_mcp_client_list_tools_real_rpc_structure():
    """
    Verify that MCPClient.list_tools correctly parses the new server endpoint response.
    """
    from agents.mcp_client import MCPClient

    client = MCPClient(mcp_url="http://mock-mcp")
    client.client = AsyncMock()

    # Simulate the response from the new list_tools bridge
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Physical alignment: Standard JSON-RPC 2.0 response format
    mock_response.json.return_value = {
        "jsonrpc": "2.0",
        "result": [{"type": "function", "function": {"name": "real_tool", "description": "desc", "parameters": {}}}],
        "id": 1,
    }
    client.client.post = AsyncMock(return_value=mock_response)

    tools = await client.list_tools()

    assert len(tools) == 1
    assert tools[0].name == "real_tool"
    # Verify the RPC call format
    args, kwargs = client.client.post.call_args
    assert kwargs["json"]["method"] == "list_tools"
