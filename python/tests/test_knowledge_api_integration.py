from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app


# Setup Global Override
def setup_module(module):
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "user-knowledge-int",
        "role": "system_admin",
        "department": "Engineering"
    }

def teardown_module(module):
    app.dependency_overrides.pop(get_current_user, None)

client = TestClient(app)

def test_summary_endpoint_performance():
    # Physically aligned patch point for KnowledgeItemService
    with patch("src.server.api_routes.knowledge.items.KnowledgeItemService") as mock_class:
        mock_inst = MagicMock()
        # Fixed: Align with service return type (success, data)
        mock_inst.get_available_sources = AsyncMock(return_value=(True, []))
        mock_class.return_value = mock_inst

        response = client.get("/api/knowledge-items/sources")
        assert response.status_code == 200

def test_error_handling_in_pagination():
    # Force a 500 error by mocking the service to return failure
    with patch("src.server.api_routes.knowledge.items.KnowledgeItemService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.list_items = AsyncMock(return_value=(False, {"error": "Database Crash"}))
        mock_class.return_value = mock_inst

        response = client.get("/api/knowledge-items")
        assert response.status_code == 500
