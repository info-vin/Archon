"""
Test Knowledge API pagination and summary endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest


class SupabaseResponse:
    """Standardized non-mock response to ensure correct JSON serialization."""
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count
        self.error = None

@pytest.fixture(autouse=True)
def bridge_dna(mock_supabase_client):
    """Global bridge for all tests in this file."""
    # 1. Create a truly infinite mock that returns itself for chaining
    infinite_mock = MagicMock()
    infinite_mock.select.return_value = infinite_mock
    infinite_mock.eq.return_value = infinite_mock
    infinite_mock.order.return_value = infinite_mock
    infinite_mock.range.return_value = infinite_mock
    infinite_mock.contains.return_value = infinite_mock
    infinite_mock.or_.return_value = infinite_mock
    infinite_mock.ilike.return_value = infinite_mock

    # 2. Setup a default successful return value for ANY execute() call
    infinite_mock.execute.return_value = SupabaseResponse(data=[], count=0)

    # 3. Bind to the client
    mock_supabase_client.table.return_value = infinite_mock
    mock_supabase_client.from_.return_value = infinite_mock

    with patch("src.server.api_routes.knowledge.items.get_supabase_client", return_value=mock_supabase_client):
        yield

def test_knowledge_summary_endpoint(client, mock_supabase_client):
    """Test the main knowledge items summary endpoint."""
    mock_sources = [{"source_id": "s1", "title": "T1", "metadata": {"knowledge_type": "technical"}}]
    # Customize the return for this specific test
    mock_supabase_client.table.return_value.execute.return_value = SupabaseResponse(data=mock_sources, count=1)

    response = client.get("/api/knowledge-items?page=1&per_page=10")
    assert response.status_code == 200
    assert "items" in response.json()

def test_chunks_pagination(client, mock_supabase_client):
    """Test document chunks pagination."""
    mock_chunks = [{"id": "c1", "content": "C1"}]
    mock_supabase_client.table.return_value.execute.return_value = SupabaseResponse(data=mock_chunks, count=50)

    response = client.get("/api/knowledge-items/test-source/chunks?page=1&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["total"] == 50

def test_pagination_limit_validation(client, mock_supabase_client):
    """Test boundary validation for pagination."""
    # Explicitly bind return value for THIS test to avoid contamination from chunks_pagination
    mock_supabase_client.table.return_value.execute.return_value = SupabaseResponse(data=[], count=0)

    response = client.get("/api/knowledge-items/test-source/chunks?limit=500&page=1")
    assert response.status_code == 200
    assert response.json()["pagination"]["per_page"] == 100

def test_empty_results_pagination(client, mock_supabase_client):
    """Test pagination behavior with no data."""
    # The default return value from bridge_dna is already empty data
    response = client.get("/api/knowledge-items/test-source/chunks?page=1&limit=10")
    assert response.status_code == 200
    assert response.json()["chunks"] == []

def test_code_examples_rag_endpoint(client, mock_supabase_client):
    """Test the RAG-based code examples endpoint (POST)."""
    mock_examples = [{"id": "e1", "content": "def test(): pass"}]
    # Note: RAGService is a separate service, needs its own patch
    with patch("src.server.services.search.rag_service.RAGService.search_code_examples_service",
               return_value=(True, mock_examples)):
        request_data = {"query": "test", "source_ids": ["test-source"], "limit": 5}
        response = client.post("/api/rag/code-examples", json=request_data)
        assert response.status_code == 200
        assert len(response.json()) > 0
