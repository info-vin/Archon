
import pytest
from unittest.mock import MagicMock
from src.agents.document_agent import DocumentAgent, DocumentDependencies

def test_list_documents_raises_name_error():
    """
    This test is designed to fail if the NameError for 'get_supabase_client'
    is NOT raised. It directly calls the problematic method to prove the bug's existence.
    This serves as a regression test once the bug is fixed.
    """
    # Arrange
    # We don't need a real model or full dependencies for this test,
    # as the NameError happens before any of them are substantially used.
    agent = DocumentAgent(model="mock-model")
    
    # Create a mock for the agent's internal PydanticAI agent
    # to isolate the tool call.
    agent.agent = MagicMock()

    # Find the actual tool function attached to the agent instance
    # This is a bit of introspection to get the real function to test
    list_documents_tool = None
    for tool in agent.agent.tools:
        if tool.__name__ == 'list_documents':
            list_documents_tool = tool
            break
    
    assert list_documents_tool is not None, "Could not find list_documents tool on agent"

    # Create mock context dependencies
    mock_deps = DocumentDependencies(project_id="test-project-id")
    mock_context = MagicMock()
    mock_context.deps = mock_deps

    # Act & Assert
    # We expect a NameError because get_supabase_client is not imported.
    # This test will PASS if the NameError is raised, and FAIL if it is not.
    with pytest.raises(NameError, match="name 'get_supabase_client' is not defined"):
        # We need to run the async tool function in a way pytest can manage.
        # Since this is a sync test function, we can create a new event loop.
        import asyncio
        asyncio.run(list_documents_tool(mock_context))
