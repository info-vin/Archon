import pytest
from unittest.mock import MagicMock, patch
from src.agents.document_agent import DocumentAgent, DocumentDependencies

# Now that the NameError is fixed, we write a proper unit test.
# We use the standard `mock_supabase_client` fixture from conftest.py
@patch('openai.OpenAI')
def test_list_documents_success(mock_openai_llm, mock_supabase_client):
    """
    Tests that the list_documents tool successfully queries and formats documents
    when the underlying database call is successful.
    """
    # Arrange
    agent = DocumentAgent(model="openai:gpt-4o")


    # Configure the mock supabase client to return mock data
    mock_response = MagicMock()
    mock_response.data = [{
        "docs": [
            {"document_type": "prd", "title": "Test PRD"},
            {"document_type": "meeting_notes", "title": "Sprint Planning"}
        ]
    }]
    mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    # Find the tool to test
    list_documents_tool = next((t for t in agent.agent.tools if t.__name__ == 'list_documents'), None)
    assert list_documents_tool is not None

    # Create mock context
    mock_context = MagicMock()
    mock_context.deps = DocumentDependencies(project_id="test-project-id")

    # Act: Run the tool
    import asyncio
    result = asyncio.run(list_documents_tool(mock_context))

    # Assert
    assert "Found 2 documents" in result
    assert "- Test PRD (prd)" in result
    assert "- Sprint Planning (meeting_notes)" in result

    # Verify that the mock was called correctly
    mock_supabase_client.table.assert_called_with("archon_projects")
    mock_supabase_client.table.return_value.select.assert_called_with("docs")
    mock_supabase_client.table.return_value.select.return_value.eq.assert_called_with("id", "test-project-id")