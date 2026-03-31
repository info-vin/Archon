from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.services.agent_service import AgentService


@pytest.fixture
def mock_mcp_client():
    client = AsyncMock()
    client.call_tool.return_value = {"status": "success", "results": "Mocked Tool Result"}
    client.search_job_market.return_value = "Found 5 React jobs"
    client.perform_rag_query.return_value = "Knowledge summary about Archon"
    return client


@pytest.mark.asyncio
async def test_run_general_agent_task_market_bot(mock_mcp_client):
    """
    [Phase 4.7 Extension] Test that MarketBot successfully runs a task and uses search_job_market tool.
    """
    service = AgentService(mcp_client=mock_mcp_client)

    mock_task = {
        "id": "t-1",
        "title": "Find React Jobs",
        "description": "Search for senior react roles in Taipei",
        "status": "todo",
    }

    mock_task_service = AsyncMock()
    mock_task_service.update_task.return_value = (True, {})
    mock_task_service.save_agent_output.return_value = (True, {})
    mock_task_service.get_task.return_value = (True, {"task": mock_task})

    mock_llm_client = AsyncMock()

    r1_msg = MagicMock()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "search_job_market"
    mock_tool_call.function.arguments = '{"query": "React Jobs"}'
    mock_tool_call.id = "call_mkt"
    r1_msg.tool_calls = [mock_tool_call]
    r1_msg.content = None

    r2_msg = MagicMock()
    r2_msg.tool_calls = None
    r2_msg.content = "I found 5 React jobs for you."

    mock_llm_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=r1_msg)]),
        MagicMock(choices=[MagicMock(message=r2_msg)]),
    ]

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_llm_client

    with (
        patch("server.services.agent_service.get_llm_client", return_value=mock_ctx),
        patch(
            "server.services.agent_service.credential_service.get_active_provider",
            return_value={"chat_model": "gpt-4o"},
        ),
        patch("server.services.projects.task_service.task_service", mock_task_service),
    ):
        await service.run_agent_task(task_id="t-1", agent_id="ai-market-bot")

        assert mock_task_service.update_task.call_count >= 2
        mock_mcp_client.search_job_market.assert_called_once()
        mock_task_service.save_agent_output.assert_called_once()
        last_call_args = mock_task_service.save_agent_output.call_args_list[-1]
        assert "I found 5 React jobs" in last_call_args.args[1]["content"]


@pytest.mark.asyncio
async def test_run_general_agent_task_librarian(mock_mcp_client):
    """
    [Phase 4.7 Extension] Test Librarian agent using RAG tool.
    """
    service = AgentService(mcp_client=mock_mcp_client)
    mock_task_service = AsyncMock()
    mock_task_service.update_task.return_value = (True, {})
    mock_task_service.save_agent_output.return_value = (True, {})
    mock_task_service.get_task.return_value = (
        True,
        {"task": {"id": "t-2", "title": "Check Specs", "description": "some desc"}},
    )

    mock_llm_client = AsyncMock()
    r1_msg = MagicMock()
    tool_call = MagicMock()
    tool_call.function.name = "perform_rag_query"
    tool_call.function.arguments = '{"query": "Archon Specs"}'
    r1_msg.tool_calls = [tool_call]

    r2_msg = MagicMock()
    r2_msg.content = "Specs are in order."

    mock_llm_client.chat.completions.create.side_effect = [
        MagicMock(choices=[MagicMock(message=r1_msg)]),
        MagicMock(choices=[MagicMock(message=r2_msg)]),
    ]

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__.return_value = mock_llm_client

    with (
        patch("server.services.agent_service.get_llm_client", return_value=mock_ctx),
        patch(
            "server.services.agent_service.credential_service.get_active_provider",
            return_value={"chat_model": "gpt-4o"},
        ),
        patch("server.services.projects.task_service.task_service", mock_task_service),
    ):
        await service.run_agent_task(task_id="t-2", agent_id="ai-librarian")
        mock_mcp_client.perform_rag_query.assert_called_once()
