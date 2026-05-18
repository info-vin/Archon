from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import src.server.services.agents.dispatcher
from src.server.services.agent_service import AgentService
from src.server.services.projects.task_service import task_service as real_task_service
from src.server.services.shared_constants import AgentUUIDs


@pytest.fixture
def mock_mcp_client():
    mock_mcp_client = AsyncMock()
    mock_mcp_client.list_tools.return_value = [
        {"function": {"name": "search_job_market", "description": "Search 104", "parameters": {}}},
        {"function": {"name": "perform_rag_query", "description": "Search DB", "parameters": {}}},
    ]
    mock_mcp_client.call_tool = AsyncMock(return_value="I found 5 React jobs")
    mock_mcp_client.perform_rag_query.return_value = "Knowledge summary about Archon"
    return mock_mcp_client


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
        patch.object(src.server.services.agents.dispatcher, "get_llm_client", return_value=mock_ctx),
        patch.object(real_task_service, "get_task", new_callable=AsyncMock, return_value=(True, {"task": mock_task})),
        patch.object(real_task_service, "update_task", new_callable=AsyncMock, return_value=(True, {})),
        patch.object(real_task_service, "save_agent_output", new_callable=AsyncMock, return_value=(True, {})),
        patch.object(src.server.services.agents.dispatcher, "credential_service") as mock_cred_svc,
    ):
        mock_cred_svc.get_credential = AsyncMock(return_value="fake_key")
        await service.run_agent_task(task_id="t-1", agent_id="market-bot", immediate=True)

        assert real_task_service.update_task.call_count >= 2
        mock_mcp_client.search_job_market.assert_called_once()
        real_task_service.save_agent_output.assert_called_once()
        last_call_args = real_task_service.save_agent_output.call_args_list[-1]
        assert "I found 5 React jobs" in last_call_args.args[1]["content"]


@pytest.mark.asyncio
async def test_run_general_agent_task_librarian(mock_mcp_client):
    """
    [Phase 4.7 Extension] Test Librarian agent using RAG tool.
    """
    service = AgentService(mcp_client=mock_mcp_client)

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
        patch.object(src.server.services.agents.dispatcher, "get_llm_client", return_value=mock_ctx),
        patch.object(real_task_service, "get_task", new_callable=AsyncMock, return_value=(True, {"task": {"id": "t-2", "title": "Check Specs", "description": "some desc"}})),
        patch.object(real_task_service, "update_task", new_callable=AsyncMock, return_value=(True, {})),
        patch.object(real_task_service, "save_agent_output", new_callable=AsyncMock, return_value=(True, {})),
        patch.object(src.server.services.agents.dispatcher, "credential_service") as mock_cred_svc,
    ):
        mock_cred_svc.get_credential = AsyncMock(return_value="fake_key")
        await service.run_agent_task(task_id="t-2", agent_id="librarian", immediate=True)
        mock_mcp_client.perform_rag_query.assert_called_once()


@pytest.mark.asyncio
async def test_run_agent_task_direct_crawler_pipeline(mock_mcp_client):
    """
    [Phase 4.6.58] Test that an empty description task with a crawler_target_id
    triggers the direct orchestrate_crawl pipeline bypassing the LLM.
    """
    service = AgentService(mcp_client=mock_mcp_client)

    mock_task = {
        "id": "t-crawl",
        "title": "Crawl Govt Site",
        "description": "",  # Empty description triggers the pipeline
        "crawler_target_id": "target-uuid-123",
        "status": "todo",
    }

    mock_supabase = MagicMock()
    mock_supabase.table().select().eq().execute.return_value.data = [
        {"id": "target-uuid-123", "target_url": "https://example.com", "max_depth": 3}
    ]

    mock_crawler = MagicMock()
    mock_crawler.orchestrate_crawl = AsyncMock(return_value={"status": "completed"})

    with (
        patch.object(src.server.services.agents.dispatcher, "get_supabase_client", return_value=mock_supabase),
        patch.object(src.server.services.agents.dispatcher, "CrawlingService", return_value=mock_crawler),
        patch.object(real_task_service, "get_task", new_callable=AsyncMock, return_value=(True, {"task": mock_task})),
        patch.object(real_task_service, "update_task", new_callable=AsyncMock, return_value=(True, {})),
        patch.object(service, "_award_agent_xp", new_callable=AsyncMock) as mock_xp,
    ):
        await service.run_agent_task(task_id="t-crawl", agent_id=AgentUUIDs.LIBRARIAN, immediate=True)

        # Verify the crawler was orchestrated with correct parameters
        mock_crawler.orchestrate_crawl.assert_called_once_with(
            {"url": "https://example.com", "max_depth": 3, "user_role": "system_admin"}
        )

        # Verify the task was marked as done directly
        real_task_service.update_task.assert_any_call("t-crawl", {"status": "done"})

        # Verify XP was awarded
        mock_xp.assert_called_once()
