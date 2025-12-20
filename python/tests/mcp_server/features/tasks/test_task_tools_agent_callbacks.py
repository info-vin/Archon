import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx
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


@pytest.fixture(autouse=True)
def mock_get_api_url():
    """Mock get_api_url to return a consistent base URL."""
    with patch("src.mcp_server.features.tasks.task_tools.get_api_url") as mock_get_url:
        mock_get_url.return_value = "http://mock-archon-server"
        yield mock_get_url


@pytest.fixture(autouse=True)
def mock_get_default_timeout():
    """Mock get_default_timeout to return a simple timeout object."""
    with patch("src.mcp_server.features.tasks.task_tools.get_default_timeout") as mock_get_timeout:
        mock_get_timeout.return_value = httpx.Timeout(5.0) # A dummy timeout for testing
        yield mock_get_timeout


@pytest.mark.asyncio
async def test_report_task_status_success(mock_mcp, mock_context):
    """Test successful reporting of task status."""
    register_task_tools(mock_mcp)
    report_tool = mock_mcp._tools.get('report_task_status')
    assert report_tool is not None, "report_task_status tool not registered"

    task_id = "test-task-123"
    status = "doing"
    agent_id = "ai-dev-agent"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "task": {"id": task_id, "status": status, "assignee": agent_id},
        "message": "Task status updated successfully"
    }

    with patch('src.mcp_server.features.tasks.task_tools.httpx.AsyncClient') as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await report_tool(mock_context, task_id=task_id, status=status, agent_id=agent_id)
        result_data = json.loads(result)

        assert result_data["success"] is True
        assert result_data["task"]["status"] == status
        mock_async_client.post.assert_called_once_with(
            f"http://mock-archon-server/api/tasks/{task_id}/agent-status",
            json={"status": status, "agent_id": agent_id}
        )


@pytest.mark.asyncio
async def test_report_task_status_api_failure(mock_mcp, mock_context):
    """Test API failure when reporting task status."""
    register_task_tools(mock_mcp)
    report_tool = mock_mcp._tools.get('report_task_status')
    assert report_tool is not None, "report_task_status tool not registered"

    task_id = "test-task-123"
    status = "doing"
    agent_id = "ai-dev-agent"

    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request: Invalid status provided"
    # Make .json() raise an error to simulate a non-JSON response body
    mock_response.json.side_effect = json.JSONDecodeError("Expecting value", "doc", 0)

    with patch('src.mcp_server.features.tasks.task_tools.httpx.AsyncClient') as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await report_tool(mock_context, task_id=task_id, status=status, agent_id=agent_id)
        result_data = json.loads(result)

        assert result_data["success"] is False
        # The formatter will now use the fallback message
        assert "Failed to report task status: HTTP 400" in result_data["error"]["message"]
        assert result_data["error"]["http_status"] == 400


@pytest.mark.asyncio
async def test_report_task_output_success(mock_mcp, mock_context):
    """Test successful reporting of task output."""
    register_task_tools(mock_mcp)
    report_tool = mock_mcp._tools.get('report_task_output')
    assert report_tool is not None, "report_task_output tool not registered"

    task_id = "test-task-123"
    output = {"summary": "Task done", "code": "print('hello')"}
    agent_id = "ai-dev-agent"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "success": True,
        "task": {"id": task_id, "status": "done", "attachments": [output]},
        "message": "Task output saved successfully"
    }

    with patch('src.mcp_server.features.tasks.task_tools.httpx.AsyncClient') as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await report_tool(mock_context, task_id=task_id, output=output, agent_id=agent_id)
        result_data = json.loads(result)

        assert result_data["success"] is True
        assert result_data["task"]["attachments"][0] == output
        mock_async_client.post.assert_called_once_with(
            f"http://mock-archon-server/api/tasks/{task_id}/agent-output",
            json={"output": output, "agent_id": agent_id}
        )


@pytest.mark.asyncio
async def test_report_task_output_network_error(mock_mcp, mock_context):
    """Test network error when reporting task output."""
    register_task_tools(mock_mcp)
    report_tool = mock_mcp._tools.get('report_task_output')
    assert report_tool is not None, "report_task_output tool not registered"

    task_id = "test-task-123"
    output = {"summary": "Task done"}
    agent_id = "ai-dev-agent"

    with patch('src.mcp_server.features.tasks.task_tools.httpx.AsyncClient') as mock_client:
        mock_async_client = AsyncMock()
        mock_async_client.post.side_effect = httpx.RequestError("Network is down", request=httpx.Request("POST", "http://mock-archon-server"))
        mock_client.return_value.__aenter__.return_value = mock_async_client

        result = await report_tool(mock_context, task_id=task_id, output=output, agent_id=agent_id)
        result_data = json.loads(result)

        assert result_data["success"] is False
        assert "request_error" in result_data["error"]["type"]
        assert "Network is down" in result_data["error"]["message"]
