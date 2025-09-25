from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient

# This test relies on the `mock_supabase_client` fixture auto-injected by `conftest.py`
# and explicitly overrides its default behavior for our specific test case.

MOCK_SOURCE_ID = "file_test_py_12345"

@patch('src.server.api_routes.knowledge_api.KnowledgeService')
def test_get_code_examples_locks_contract(mock_knowledge_service_class, client: TestClient):
    """
    Tests the contract for the get_knowledge_item_code_examples endpoint.
    It mocks the KnowledgeService to isolate the test from the database, following
    the established pattern in `test_settings_api.py`.
    """
    # Arrange: Configure the mock service's method to return mock data
    mock_instance = mock_knowledge_service_class.return_value
    MOCK_CODE_EXAMPLES = [{"id": "ex_1"}]
    mock_instance.get_code_examples = AsyncMock(return_value=MOCK_CODE_EXAMPLES)

    # Act
    response = client.get(f"/api/knowledge-items/{MOCK_SOURCE_ID}/code-examples")

    # Assert
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["code_examples"][0]["id"] == "ex_1"

    # Verify that the service method was called correctly
    mock_instance.get_code_examples.assert_called_once_with(MOCK_SOURCE_ID)