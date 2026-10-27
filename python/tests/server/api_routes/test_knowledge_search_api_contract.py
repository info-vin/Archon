from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO

client = TestClient(app)


@pytest.fixture
def mock_user():
    user = {"id": "user_contract_1", "role": "employee", "email": "contractor@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(**user)
    yield user
    app.dependency_overrides.pop(get_current_user, None)


def test_search_knowledge_items_contract(mock_user):
    """Verify that search_knowledge_items preserves producer dict fields and metadata without stripping."""
    mock_search_results = [
        {
            "id": 101,
            "url": "https://docs.archon.com/guide/setup",
            "chunk_number": 2,
            "content": "Archon installation and setup guide",
            "metadata": {
                "category": "setup",
                "custom_tag": "v2.0",
                "nested": {"author": "Archon Team"},
            },
            "source_id": "src_setup_01",
            "similarity": 0.892,
            "extra_jsonb_field": "unmapped_producer_data",
        }
    ]

    with patch("src.server.api_routes.knowledge.search.RAGService") as mock_rag_class:
        mock_instance = AsyncMock()
        mock_instance.search_documents = AsyncMock(return_value=mock_search_results)
        mock_rag_class.return_value = mock_instance

        payload = {"query": "how to setup archon", "source_ids": ["src_setup_01"], "limit": 5}
        response = client.post("/api/knowledge-items/search", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1

        item = data[0]
        assert item["id"] == 101
        assert item["url"] == "https://docs.archon.com/guide/setup"
        assert item["chunk_number"] == 2
        assert item["content"] == "Archon installation and setup guide"
        assert item["metadata"]["category"] == "setup"
        assert item["metadata"]["nested"]["author"] == "Archon Team"
        assert item["source_id"] == "src_setup_01"
        assert item["similarity"] == 0.892
        # Extra JSONB/unmapped field preserved due to ConfigDict(extra="allow")
        assert item["extra_jsonb_field"] == "unmapped_producer_data"
