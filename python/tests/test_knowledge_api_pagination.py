from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO


# Setup Global Override for Knowledge Tests
def setup_module(module):
    # Provide system_admin identity to pass through RBAC seals
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(id="user-knowledge", role="system_admin", email="mock@archon.com", department="Engineering")


def teardown_module(module):
    app.dependency_overrides.pop(get_current_user, None)


client = TestClient(app)


def test_knowledge_summary_endpoint():
    # Physically aligned patch point for KnowledgeItemService
    with patch("src.server.api_routes.knowledge.items.KnowledgeItemService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.get_available_sources = AsyncMock(return_value=(True, []))
        mock_class.return_value = mock_inst

        response = client.get("/api/knowledge-items/sources")
        assert response.status_code == 200


def test_chunks_pagination():
    # Chunks are delegated to KnowledgeSummaryService
    with patch("src.server.api_routes.knowledge.items.KnowledgeSummaryService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.get_item_chunks = AsyncMock(return_value=(True, []))
        mock_class.return_value = mock_inst

        response = client.get("/api/knowledge-items/source-1/chunks")
        assert response.status_code == 200


def test_pagination_limit_validation():
    # Smoke test connectivity with identity override
    with patch("src.server.api_routes.knowledge.items.KnowledgeItemService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.list_items = AsyncMock(return_value=(True, []))
        mock_class.return_value = mock_inst
        response = client.get("/api/knowledge-items?per_page=10")
        assert response.status_code == 200


def test_empty_results_pagination():
    with patch("src.server.api_routes.knowledge.items.KnowledgeItemService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.list_items = AsyncMock(return_value=(True, []))
        mock_class.return_value = mock_inst
        response = client.get("/api/knowledge-items?page=100")
        assert response.status_code == 200


def test_code_examples_rag_endpoint():
    # Use search path - Path the Service Logic in the search module
    with patch("src.server.api_routes.knowledge.search.RAGService") as mock_class:
        mock_inst = MagicMock()
        mock_inst.search_code_examples_service = AsyncMock(return_value=(True, []))
        mock_class.return_value = mock_inst

        # Aligned with physical search path
        response = client.post("/api/code-examples", json={"query": "test"})
        assert response.status_code == 200
