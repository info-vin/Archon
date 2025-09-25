from unittest.mock import MagicMock
from fastapi.testclient import TestClient

# This test relies on the `mock_supabase_client` fixture auto-injected by `conftest.py`
# and explicitly overrides its default behavior for our specific test case.

MOCK_SOURCE_ID = "file_test_py_12345"

def test_get_code_examples_locks_contract(client: TestClient, mock_supabase_client: MagicMock):
    """
    Tests the contract for the get_knowledge_item_code_examples endpoint.
    It overrides the global mock provided by conftest.py.
    """
    # Arrange: Create a mock response object
    MOCK_CODE_EXAMPLES = [{"id": "ex_1"}]
    mock_response = MagicMock()
    mock_response.data = MOCK_CODE_EXAMPLES
    
    # Arrange: Override the default mock behavior from conftest.py for this specific call
    # The autouse fixture in conftest.py sets the default return value for execute().data to [].
    # We must override it here to return our desired mock data for this test.
    mock_supabase_client.from_.return_value.select.return_value.eq.return_value.execute.return_value = mock_response

    # Act
    response = client.get(f"/api/knowledge-items/{MOCK_SOURCE_ID}/code-examples")

    # Assert
    assert response.status_code == 200
    response_json = response.json()
    assert response_json["count"] == 1
    assert response_json["code_examples"][0]["id"] == "ex_1"