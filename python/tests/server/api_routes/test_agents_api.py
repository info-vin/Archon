from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

# It's important to patch the service BEFORE it's imported by the app
# so that the router gets the mocked dependency
mock_agent_service = AsyncMock()
mock_agent_service.get_assignable_agents.return_value = [
    {"id": "ai-tester-1", "name": "測試 AI Agent", "role": "TEST"},
]

# The patch needs to target where the object is *used*, which is in the api_routes module
module_patch = patch(
    'src.server.api_routes.agents_api.agent_service',
    mock_agent_service
)

# Now we can import the app
from src.server.main import app  # noqa: E402

# Start the patch AFTER the app is imported
module_patch.start()

client = TestClient(app)


def test_get_assignable_agents_success():
    """
    Test successfully fetching the list of assignable agents.
    """
    response = client.get("/api/agents/assignable")

    # Assertions
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "ai-tester-1"
    assert data[0]["name"] == "測試 AI Agent"

    # Verify that the mocked service method was called
    mock_agent_service.get_assignable_agents.assert_awaited_once()

def test_get_assignable_agents_service_error():
    """
    Test handling of an error from the agent service.
    """
    # Reset and configure the mock for this specific test
    mock_agent_service.reset_mock()
    mock_agent_service.get_assignable_agents.side_effect = Exception("Service unavailable")

    response = client.get("/api/agents/assignable")

    # Assert that the app's exception handler caught it (FastAPI returns 500)
    assert response.status_code == 500
    assert "Failed to retrieve assignable agents" in response.text

    # Clean up the side effect
    mock_agent_service.get_assignable_agents.side_effect = None
    mock_agent_service.reset_mock()
    # Restore the original return value for other tests if needed
    mock_agent_service.get_assignable_agents.return_value = [
        {"id": "ai-tester-1", "name": "測試 AI Agent", "role": "TEST"},
    ]

# Stop the patch after all tests in this module are done
def teardown_module(module):
    module_patch.stop()
