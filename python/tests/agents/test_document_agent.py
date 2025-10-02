from unittest.mock import MagicMock, patch

import pytest
from pydantic_ai import models
from pydantic_ai.models.test import TestModel

from src.agents.document_agent import DocumentAgent, DocumentDependencies

# Per official pydantic-ai docs, this prevents accidental real LLM calls during tests
models.ALLOW_MODEL_REQUESTS = False
pytestmark = pytest.mark.anyio


# We patch `get_supabase_client` at the location where it's looked up by the agent code.
@patch('src.agents.document_agent.get_supabase_client')
def test_list_documents_success(mock_get_supabase_client, mock_supabase_client):
    """
    Tests that the list_documents tool successfully queries and formats documents
    when the underlying database call is successful, using pydantic-ai's recommended testing patterns.
    """
    # Arrange:
    # 1. Configure the mock for get_supabase_client to return our fixture
    mock_get_supabase_client.return_value = mock_supabase_client

    # 2. Instantiate the agent. The model will be overridden, so the exact value doesn't matter.
    agent = DocumentAgent(model="openai:gpt-4o")

    # 3. Configure the mock supabase client (from conftest.py) to return mock data
    mock_response = MagicMock()
    mock_response.data = [{
        "docs": [
            {"document_type": "prd", "title": "Test PRD"},
            {"document_type": "meeting_notes", "title": "Sprint Planning"}
        ]
    }]
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    # 4. Find the tool to test from the agent's tool list
    # By inspecting agent.agent.__dict__, we found the tools are stored in the `_function_tools`
    # dictionary, where the key is the tool name and the value is a Tool object.
    # The actual callable is the .function attribute of the Tool object.
    list_documents_tool = agent.agent._function_tools['list_documents'].function
    assert list_documents_tool is not None

    # 5. Create mock context that the tool expects
    mock_context = MagicMock()
    mock_context.deps = DocumentDependencies(project_id="test-project-id")

    # Act: Run the tool within the agent.agent.override context as recommended by pydantic-ai docs.
    # This replaces the real LLM with a predictable TestModel. The .override() method belongs to
    # the nested pydantic-ai Agent, not our wrapper class.
    with agent.agent.override(model=TestModel()):
        import asyncio
        result = asyncio.run(list_documents_tool(mock_context))

    # Assert
    assert "Found 2 documents" in result
    assert "- Test PRD (prd)" in result
    assert "- Sprint Planning (meeting_notes)" in result

    # Verify that the mock was called correctly
    mock_get_supabase_client.assert_called_once()
    mock_supabase_client.table.assert_called_with("archon_projects")
    mock_supabase_client.table.return_value.select.assert_called_with("docs")
    mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with("id", "test-project-id")
