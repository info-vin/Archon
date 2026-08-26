from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.agents.dispatcher import DailyMarketReportStrategy, agent_dispatcher
from src.server.services.marketing.blog_generator import BlogGenerator
from src.server.services.shared_constants import AgentUUIDs


@pytest.mark.asyncio
async def test_dispatcher_routes_to_daily_market_report_strategy():
    """Verify that AgentDispatcher routes 'Daily Market Intelligence' tasks to DailyMarketReportStrategy."""
    task_data = {
        "title": "Daily Market Intelligence (2026-08-26)",
        "description": "Some description"
    }
    strategy = agent_dispatcher.get_strategy(AgentUUIDs.MARKET_BOT, task_data)
    assert isinstance(strategy, DailyMarketReportStrategy)

@pytest.mark.asyncio
@patch("src.server.services.marketing.content_handler.ContentHandler")
@patch("src.server.services.projects.task_service.task_service", new_callable=AsyncMock)
async def test_daily_market_report_strategy_execute_success(mock_task_service, MockContentHandler):
    """Verify that DailyMarketReportStrategy executes the handler and updates task."""
    mock_handler_instance = MockContentHandler.return_value
    mock_handler_instance.blog_generator = MagicMock()
    mock_handler_instance.blog_generator.draft_daily_market_report_physical = AsyncMock(return_value="Success msg")

    mock_agent_service = AsyncMock()

    strategy = DailyMarketReportStrategy()
    task_id = "test-task-123"
    task_data = {"id": task_id, "title": "Daily Market Intelligence"}

    await strategy.execute(task_id, task_data, AgentUUIDs.MARKET_BOT, mock_agent_service)

    mock_handler_instance.blog_generator.draft_daily_market_report_physical.assert_awaited_once_with(task_id, task_data)
    mock_task_service.update_task.assert_awaited_once_with(task_id, {"status": "done"})
    mock_agent_service._award_agent_xp.assert_awaited_once_with(AgentUUIDs.MARKET_BOT, task_data, "Success msg")

@pytest.mark.asyncio
@patch("src.server.services.marketing.blog_generator.genai.Client")
@patch("src.server.services.credential_service.credential_service.get_credential", new_callable=AsyncMock)
@patch("src.server.services.marketing.blog_generator.prompt_service.get_prompt")
async def test_blog_generator_draft_daily_market_report_physical(mock_get_prompt, mock_get_credential, MockGenaiClient):
    """Verify physical execution inserts a blog post via supabase."""
    # Setup mocks
    mock_get_credential.return_value = "fake-api-key"
    mock_get_prompt.return_value = "Fake prompt"

    mock_client_instance = MockGenaiClient.return_value
    mock_generate = AsyncMock()
    mock_response = MagicMock()
    mock_response.text = '{"title": "Test Report", "content": "Test Content", "excerpt": "Test"}'
    mock_generate.return_value = mock_response
    mock_client_instance.aio.models.generate_content = mock_generate

    mock_supabase = MagicMock()
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_table.insert.return_value = mock_table # for chaining

    # Need to patch BaseRepository.execute_query since it executes the insert
    generator = BlogGenerator(mock_supabase)

    with patch.object(generator, "execute_query", return_value=(True, {"data": []})):
        task_data = {"title": "Daily Market Intelligence (Test)", "description": "Raw data goes here"}
        result = await generator.draft_daily_market_report_physical("task-123", task_data)

        assert "Successfully generated" in result

        # Verify LLM was called
        mock_generate.assert_awaited_once()
        args, kwargs = mock_generate.call_args
        assert "Raw data goes here" in kwargs["contents"]

        # Verify db insert was called
        mock_supabase.table.assert_called_once_with("blog_posts")
        mock_table.insert.assert_called_once()
        insert_payload = mock_table.insert.call_args[0][0]
        assert insert_payload["title"] == "Test Report"
        assert insert_payload["content"] == "Test Content"
        assert insert_payload["status"] == "draft"
