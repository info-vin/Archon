from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.prompts.dev_ops_prompts import DEVBOT_TOOLS
from src.server.schemas.tool_schemas import SearchCodeArgs
from src.server.services.agent_service import AgentService


@pytest.mark.asyncio
class TestDevBotSkills:
    async def test_tool_schemas_integrity(self):
        """Verify Pydantic schemas generate correct JSON schemas for LLM."""
        # check SearchCodeArgs
        schema = SearchCodeArgs.model_json_schema()
        assert "query" in schema["properties"]
        assert schema["properties"]["query"]["type"] == "string"

        # Check DEVBOT_TOOLS integration
        search_tool = next(t for t in DEVBOT_TOOLS if t["function"]["name"] == "search_code_examples")
        assert search_tool["function"]["parameters"]["properties"]["query"]["type"] == "string"

    @patch("src.server.services.agent_service.get_llm_client")
    async def test_devbot_auto_repair_loop_mocked(self, mock_get_client):
        """
        Test the 'Two-pass' loop in _analyze_error_with_structured_output.
        We simulate:
        1. LLM sees error -> Proposes 'search_code_examples' tool call.
        2. AgentService executes tool -> Returns 'Found code...'.
        3. LLM sees tool result -> Proposes final JSON fix.
        """
        service = AgentService(mcp_client=AsyncMock())

        # --- Mock LLM Responses ---
        mock_client_instance = AsyncMock()
        mock_get_client.return_value.__aenter__.return_value = mock_client_instance

        # Round 1 Response: Call Tool
        # valid ToolCall mock must have function.name as a string
        mock_function = MagicMock()
        mock_function.name = "search_code_examples"
        mock_function.arguments = '{"query": "AttributeError"}'

        msg_tool_call = MagicMock()
        msg_tool_call.tool_calls = [MagicMock(id="call_123", function=mock_function)]
        msg_tool_call.content = None

        # Round 2 Response: Final JSON
        msg_final = MagicMock()
        msg_final.tool_calls = None
        msg_final.content = '{"file_path": "test.py", "fixed_content": "fixed", "reasoning": "fixed it"}'

        # Setup side_effect for chat.completions.create
        # First call -> Tool Call, Second call -> Final JSON
        mock_client_instance.chat.completions.create.side_effect = [
            MagicMock(choices=[MagicMock(message=msg_tool_call)]),
            MagicMock(choices=[MagicMock(message=msg_final)]),
        ]

        # --- Mock Tool Execution ---
        # We assume self.mcp_client.search_code_examples will be called
        service.mcp_client.search_code_examples.return_value = "Found definition of error"

        # --- Execute ---
        result = await service._analyze_error_with_structured_output("cmd", "error", agent_id="ai-dev-bot")

        # --- Verify ---
        assert result is not None
        assert result["file_path"] == "test.py"
        assert result["fixed_content"] == "fixed"

        # Verify Tool was actually called
        service.mcp_client.search_code_examples.assert_called_once_with(query="AttributeError")
