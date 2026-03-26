import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.server.fastmcp import Context

from src.mcp_server.features.tasks.task_tools import register_task_tools


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server for testing."""
    mock = MagicMock()
    # Store registered tools
    mock._tools = {}

    def tool_decorator():
        def decorator(func):
            mock._tools[func.__name__] = func
            return func
        return decorator

    mock.tool = tool_decorator
    return mock


@pytest.fixture
def mock_context():
    """Create a mock context for testing."""
    return MagicMock(spec=Context)


@pytest.mark.asyncio
async def test_report_task_status_success(mock_mcp, mock_context):
    """Test successful reporting of task status."""
    register_task_tools(mock_mcp)
    report_tool = mock_mcp._tools.get('report_task_status')
    assert report_tool is not None, "report_task_status tool not registered"

    task_id = "test-task-123"
    status = "doing"
    agent_id = "ai-dev-agent"

    # Mock call_api response
    mock_res = {
        "success": True,
        "task": {"id": task_id, "status": status, "assignee": agent_id},
        "message": "Task status updated successfully"
    }

    with patch("src.mcp_server.features.tasks.task_tools.call_api", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_res

        result = await report_tool(mock_context, task_id=task_id, status=status, agent_id=agent_id)
        result_data = json.loads(result)

        assert result_data["success"] is True
        assert result_data["task"]["status"] == status

        # Verify call_api details
        args, kwargs = mock_call.call_args
        assert args[0] == "POST"
        assert args[1] == f"/api/tasks/{task_id}/agent-status"
        assert kwargs["json"]["status"] == status


@pytest.mark.asyncio
async def test_report_task_status_api_failure(mock_mcp, mock_context):
    """Test API failure when reporting task status."""
    register_task_tools(mock_mcp)
    report_tool = mock_mcp._tools.get('report_task_status')

    task_id = "test-task-123"

    # Mock call_api failure
    mock_res = {
        "success": False,
        "error": "HTTP 400: Bad Request"
    }

    with patch("src.mcp_server.features.tasks.task_tools.call_api", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_res

        result = await report_tool(mock_context, task_id=task_id, status="invalid", agent_id="agent")
        result_data = json.loads(result)

        assert result_data["success"] is False
        assert "HTTP 400" in result_data["error"]


@pytest.mark.asyncio
async def test_report_task_output_success(mock_mcp, mock_context):
    """Test successful reporting of task output."""
    register_task_tools(mock_mcp)
    report_tool = mock_mcp._tools.get('report_task_output')

    task_id = "test-task-123"
    output = {"summary": "Task done"}
    agent_id = "ai-dev-agent"

    mock_res = {
        "success": True,
        "task": {"id": task_id, "status": "done", "attachments": [output]},
        "message": "Task output saved successfully"
    }

    with patch("src.mcp_server.features.tasks.task_tools.call_api", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_res

        result = await report_tool(mock_context, task_id=task_id, output=output, agent_id=agent_id)
        result_data = json.loads(result)

        assert result_data["success"] is True
        assert result_data["task"]["attachments"][0] == output

        # Verify call_api details
        args, kwargs = mock_call.call_args
        assert args[1] == f"/api/tasks/{task_id}/agent-output"
        assert kwargs["json"]["output"] == output


@pytest.mark.asyncio
async def test_report_task_output_network_error(mock_mcp, mock_context):
    """Test network error (exception) when reporting task output."""
    register_task_tools(mock_mcp)
    report_tool = mock_mcp._tools.get('report_task_output')

    with patch("src.mcp_server.features.tasks.task_tools.call_api", new_callable=AsyncMock) as mock_call:
        # call_api itself handles exceptions and returns a success=False dict
        mock_call.return_value = {
            "success": False,
            "error": "Connection refused"
        }

        result = await report_tool(mock_context, task_id="t1", output={}, agent_id="a1")
        result_data = json.loads(result)

        assert result_data["success"] is False
        assert "Connection refused" in result_data["error"]
