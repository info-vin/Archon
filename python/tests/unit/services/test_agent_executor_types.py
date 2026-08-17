import pytest
from unittest.mock import MagicMock
from src.server.services.agent_tool_executor import AgentToolExecutor
from src.server.services.agent_service import AgentService

@pytest.mark.asyncio
async def test_agent_executor_init():
    mock_mcp = MagicMock()
    executor = AgentToolExecutor(mock_mcp)
    assert executor.mcp_client == mock_mcp

    service = AgentService(mock_mcp)
    assert service.mcp_client == mock_mcp
