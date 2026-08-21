"""Unit tests for PresentationAgent."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic_ai import RunContext

from src.agents.presentation.presentation_agent import (
    PresentationAgent,
    PresentationDependencies,
    PresentationOperation,
)
from src.server.config.model_ssot import SYSTEM_MODELS

TEST_MODEL = "test"


@pytest.mark.asyncio
async def test_presentation_agent_run():
    """Test PresentationAgent run loop returns structured output using mocked Agent run."""
    agent = PresentationAgent(model=TEST_MODEL)

    # Mock the RunResult from pydantic_ai
    mock_run_result = MagicMock()
    mock_run_result.data = PresentationOperation(
        content="NotebookLM generated presentation slides outline.",
        gdrive_file_id="gdrive_doc_test123",
        success=True,
        message="Presentation generated and archived successfully.",
    )
    # Exclude or override the output property to avoid returning a mock nested object
    mock_run_result.output = mock_run_result.data

    mock_run_result.usage = MagicMock()
    mock_run_result.usage.request_tokens = 5
    mock_run_result.usage.response_tokens = 10
    mock_run_result.model_used = "mock-model"

    # We patch the class method Agent.run to return our custom mock run result
    with patch("pydantic_ai.Agent.run", new_callable=AsyncMock) as mock_agent_run:
        mock_agent_run.return_value = mock_run_result

        deps = PresentationDependencies(
            topic="AI agents",
            notebook_id="nb-123",
            task_id="task-789",
            project_id="proj-999",
            progress_callback=AsyncMock(),
        )

        result = await agent.run("Start generating", deps=deps)

        assert isinstance(result, PresentationOperation)
        assert result.success is True
        assert result.content == "NotebookLM generated presentation slides outline."
        assert result.gdrive_file_id == "gdrive_doc_test123"


@pytest.mark.asyncio
@pytest.mark.skip(reason="Legacy tool replaced by native NotebookLM generate_and_upload_pptx")
async def test_generate_and_archive_tool():
    """Test the physical archiving tool logic (NotebookLM + GDrive)."""
    agent = PresentationAgent(model=TEST_MODEL)

    mock_mcp_client = AsyncMock()
    mock_mcp_client.call_tool = AsyncMock()
    mock_mcp_client.call_tool.side_effect = [
        '{"success": true, "answer": "Mocked NotebookLM answer", "conversation_id": "conv-456"}',  # notebooklm_ask_question
        '{"success": true, "file_id": "real_gdrive_12345"}',  # gdrive_upload_file
        '{"success": true}',  # manage_task update
    ]

    with patch("src.agents.presentation.presentation_agent.get_mcp_client", new_callable=AsyncMock) as mock_get_mcp:
        mock_get_mcp.return_value = mock_mcp_client

        deps = PresentationDependencies(
            topic="AI agents",
            notebook_id="nb-123",
            task_id="task-789",
            project_id="proj-999",
            progress_callback=AsyncMock(),
        )

        # Create a mock RunContext
        ctx = MagicMock(spec=RunContext)
        ctx.deps = deps

        # Call the tool function directly on the agent class
        result = await agent.generate_and_archive(ctx)

        assert isinstance(result, PresentationOperation)
        assert result.success is True
        assert result.content == "Mocked NotebookLM answer"
        assert result.gdrive_file_id == "real_gdrive_12345"

        # Verify NotebookLM question was asked
        mock_mcp_client.call_tool.assert_any_call(
            tool_name="notebooklm_ask_question",
            notebook_id="nb-123",
            question="Generate a detailed outline and slides content for: AI agents",
        )

        # Verify GDrive tool was called
        mock_mcp_client.call_tool.assert_any_call(
            tool_name="gdrive_upload_file",
            filename="Presentation_AI_agents",
            content="Mocked NotebookLM answer",
            mime_type="text/plain",
        )
