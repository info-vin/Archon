"""Unit tests for NotebookLM MCP tools."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.server.fastmcp import Context

from src.mcp_server.features.notebooklm.notebooklm_tools import register_notebooklm_tools


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server for testing."""
    mock = MagicMock()
    mock._tools = {}

    def tool_decorator(*args, **kwargs):
        def decorator(func):
            mock._tools[func.__name__] = func
            return func

        return decorator

    mock.tool = tool_decorator
    return mock


@pytest.fixture
def mock_context():
    """Create a mock context with ArchonContext lifespan_context."""
    context = MagicMock(spec=Context)

    # Mock client and app_state/lifespan_context
    mock_client = MagicMock()

    # Setup mock methods
    mock_client.notebooks = MagicMock()
    mock_client.notebooks.list = AsyncMock()
    mock_client.notebooks.create = AsyncMock()

    mock_client.chat = MagicMock()
    mock_client.chat.ask = AsyncMock()

    context.request_context.lifespan_context.client = mock_client
    return context, mock_client


@pytest.mark.asyncio
async def test_notebooklm_list_notebooks(mock_mcp, mock_context):
    """Test listing notebooks tool."""
    ctx, client = mock_context
    register_notebooklm_tools(mock_mcp)

    list_notebooks = mock_mcp._tools.get("notebooklm_list_notebooks")
    assert list_notebooks is not None

    # Setup mock return value
    mock_nb1 = MagicMock()
    mock_nb1.id = "nb-1"
    mock_nb1.title = "Test Notebook"
    mock_nb1.sources_count = 3
    mock_nb1.created_at = "2026-08-20T10:00:00"

    client.notebooks.list.return_value = [mock_nb1]

    res_str = await list_notebooks(ctx)
    res = json.loads(res_str)

    assert res["success"] is True
    assert len(res["notebooks"]) == 1
    assert res["notebooks"][0]["id"] == "nb-1"
    assert res["notebooks"][0]["title"] == "Test Notebook"


@pytest.mark.asyncio
async def test_notebooklm_create_notebook(mock_mcp, mock_context):
    """Test creating notebook tool."""
    ctx, client = mock_context
    register_notebooklm_tools(mock_mcp)

    create_notebook = mock_mcp._tools.get("notebooklm_create_notebook")
    assert create_notebook is not None

    mock_nb = MagicMock()
    mock_nb.id = "nb-new"
    mock_nb.title = "New Notebook"
    client.notebooks.create.return_value = mock_nb

    res_str = await create_notebook(ctx, title="New Notebook")
    res = json.loads(res_str)

    assert res["success"] is True
    assert res["notebook_id"] == "nb-new"
    client.notebooks.create.assert_called_once_with("New Notebook")


@pytest.mark.asyncio
async def test_notebooklm_ask_question(mock_mcp, mock_context):
    """Test asking question tool."""
    ctx, client = mock_context
    register_notebooklm_tools(mock_mcp)

    ask_question = mock_mcp._tools.get("notebooklm_ask_question")
    assert ask_question is not None

    mock_res = MagicMock()
    mock_res.answer = "This is the answer."
    mock_res.conversation_id = "conv-1"
    client.chat.ask.return_value = mock_res

    res_str = await ask_question(ctx, notebook_id="nb-1", question="What is testing?")
    res = json.loads(res_str)

    assert res["success"] is True
    assert res["answer"] == "This is the answer."
    assert res["conversation_id"] == "conv-1"
    client.chat.ask.assert_called_once_with("nb-1", "What is testing?")

@pytest.mark.asyncio
async def test_official_tools_registration(mock_mcp):
    """Test that official notebooklm-py tools are registered via Monkey Patch."""
    register_notebooklm_tools(mock_mcp)

    # Assert at least some of the official tools were registered
    assert "notebooks_list" in mock_mcp._tools or "chat_ask" in mock_mcp._tools or "sources_list" in mock_mcp._tools or "notebook_list" in mock_mcp._tools

    # We also check that our custom wrapper tools are still registered
    assert "notebooklm_list_notebooks" in mock_mcp._tools
