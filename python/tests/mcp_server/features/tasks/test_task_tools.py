"""Unit tests for task management tools."""

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
async def test_create_task_with_sources(mock_mcp, mock_context):
    """Test creating a task using manage_task."""
    register_task_tools(mock_mcp)

    # Get the manage_task function
    manage_task = mock_mcp._tools.get("manage_task")

    assert manage_task is not None, "manage_task tool not registered"

    # Mock call_api response
    mock_res = {
        "success": True,
        "task": {"id": "task-123", "title": "Test Task"},
        "message": "Task created successfully",
    }

    with patch("src.mcp_server.features.tasks.task_tools.call_api", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_res

        result = await manage_task(
            mock_context,
            action="create",
            project_id="project-123",
            title="Implement OAuth2",
            description="Add OAuth2 authentication",
            assignee="AI IDE Agent",
        )

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["task_id"] == "task-123"

        # Verify the task was created properly via call_api
        mock_call.assert_called_once()
        args, kwargs = mock_call.call_args
        assert args[0] == "POST"
        assert args[1] == "/api/tasks"
        assert kwargs["json"]["title"] == "Implement OAuth2"


@pytest.mark.asyncio
async def test_find_tasks_with_project_filter(mock_mcp, mock_context):
    """Test listing tasks with project-specific endpoint."""
    register_task_tools(mock_mcp)

    # Get the find_tasks function
    find_tasks = mock_mcp._tools.get("find_tasks")

    assert find_tasks is not None, "find_tasks tool not registered"

    # Mock call_api response
    mock_res = {
        "success": True,
        "tasks": [
            {"id": "task-1", "title": "Task 1", "status": "todo"},
            {"id": "task-2", "title": "Task 2", "status": "doing"},
        ]
    }

    with patch("src.mcp_server.features.tasks.task_tools.call_api", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_res

        result = await find_tasks(
            mock_context,
            filter_by="project",
            filter_value="project-123"
        )

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert len(result_data["tasks"]) == 2

        # Verify the correct project endpoint was called
        args, kwargs = mock_call.call_args
        assert args[1] == "/api/projects/project-123/tasks"


@pytest.mark.asyncio
async def test_find_tasks_with_status_filter(mock_mcp, mock_context):
    """Test listing tasks with status filter."""
    register_task_tools(mock_mcp)

    # Get the find_tasks function
    find_tasks = mock_mcp._tools.get("find_tasks")

    # Mock call_api response
    mock_res = {
        "success": True,
        "tasks": [
            {"id": "task-1", "title": "Task 1", "status": "todo"},
        ]
    }

    with patch("src.mcp_server.features.tasks.task_tools.call_api", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_res

        result = await find_tasks(
            mock_context,
            filter_by="status",
            filter_value="todo"
        )

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["tasks"][0]["status"] == "todo"

        # Verify status parameter was passed
        args, kwargs = mock_call.call_args
        assert kwargs["params"]["status"] == "todo"


@pytest.mark.asyncio
async def test_update_task_status(mock_mcp, mock_context):
    """Test updating task status."""
    register_task_tools(mock_mcp)
    manage_task = mock_mcp._tools.get("manage_task")

    # Mock call_api response
    mock_res = {
        "success": True,
        "task": {"id": "task-123", "status": "doing"},
        "message": "Task updated successfully",
    }

    with patch("src.mcp_server.features.tasks.task_tools.call_api", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_res

        result = await manage_task(
            mock_context,
            action="update",
            task_id="task-123",
            status="doing"
        )

        result_data = json.loads(result)
        assert result_data["success"] is True
        assert result_data["task"]["status"] == "doing"

        # Verify PUT call
        args, kwargs = mock_call.call_args
        assert args[0] == "PUT"
        assert args[1] == "/api/tasks/task-123"
        assert kwargs["json"]["status"] == "doing"


@pytest.mark.asyncio
async def test_delete_task_already_archived(mock_mcp, mock_context):
    """Test deleting an already archived/deleted task."""
    register_task_tools(mock_mcp)
    manage_task = mock_mcp._tools.get("manage_task")

    # Mock call_api 404 response
    mock_res = {
        "success": False,
        "error": "HTTP 404: Not Found"
    }

    with patch("src.mcp_server.features.tasks.task_tools.call_api", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_res

        result = await manage_task(
            mock_context,
            action="delete",
            task_id="task-none"
        )

        result_data = json.loads(result)
        assert result_data["success"] is False
        assert "HTTP 404" in result_data["error"]
