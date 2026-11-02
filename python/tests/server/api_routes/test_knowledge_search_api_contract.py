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


def test_perform_rag_query_contract(mock_user):
    """Verify that perform_rag_query preserves producer dict fields and metadata without stripping."""
    mock_rag_query_result = {
        "results": [
            {
                "id": "result_0",
                "content": "RAG pipeline search result excerpt.",
                "metadata": {"source": "https://archon.com/docs", "tags": ["policy"]},
                "similarity_score": 0.95,
                "extra_item_attribute": "preserved",
            }
        ],
        "query": "archon rag query",
        "source": "https://archon.com/docs",
        "match_count": 5,
        "total_found": 1,
        "execution_path": "rag_service_pipeline",
        "search_mode": "hybrid",
        "reranking_applied": True,
        "custom_pipeline_metadata": {"version": "2.1"},
    }

    with patch("src.server.api_routes.knowledge.search.RAGService") as mock_rag_class:
        mock_instance = AsyncMock()
        mock_instance.perform_rag_query = AsyncMock(return_value=(True, mock_rag_query_result))
        mock_rag_class.return_value = mock_instance

        payload = {"query": "archon rag query", "limit": 5}
        response = client.post("/api/rag/query", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["query"] == "archon rag query"
        assert data["search_mode"] == "hybrid"
        assert data["reranking_applied"] is True
        assert data["total_found"] == 1
        assert len(data["results"]) == 1
        result_item = data["results"][0]
        assert result_item["id"] == "result_0"
        assert result_item["similarity_score"] == 0.95
        assert result_item["extra_item_attribute"] == "preserved"
        assert data["custom_pipeline_metadata"]["version"] == "2.1"


def test_perform_rag_query_mcp_caller_contract(mock_user):
    """Verify that perform_rag_query correctly translates MCP tool parameter shapes (source, match_count)."""
    mock_rag_query_result = {
        "results": [],
        "query": "mcp tool query",
        "source": "src_mcp_domain",
        "match_count": 8,
        "total_found": 0,
        "execution_path": "rag_service_pipeline",
        "search_mode": "vector",
        "reranking_applied": False,
    }

    with patch("src.server.api_routes.knowledge.search.RAGService") as mock_rag_class:
        mock_instance = AsyncMock()
        mock_instance.perform_rag_query = AsyncMock(return_value=(True, mock_rag_query_result))
        mock_rag_class.return_value = mock_instance

        # Payload structure passed by rag_tools.py: {"query": ..., "source": ..., "match_count": ...}
        payload = {"query": "mcp tool query", "source": "src_mcp_domain", "match_count": 8}
        response = client.post("/api/rag/query", json=payload)

        assert response.status_code == 200
        # Verify RAGService received effective_source and effective_limit mapped from MCP params
        mock_instance.perform_rag_query.assert_called_once_with(
            query="mcp tool query", source="src_mcp_domain", match_count=8
        )
        data = response.json()
        assert data["success"] is True
        assert data["source"] == "src_mcp_domain"
        assert data["match_count"] == 8


def test_search_code_examples_contract(mock_user):
    """Verify that search_code_examples (/api/rag/code-examples) preserves realistic producer fields and extra JSONB."""
    mock_code_search_result = {
        "query": "def calculate_tax",
        "source_filter": "src_tax_repo",
        "search_mode": "hybrid",
        "reranking_applied": True,
        "results": [
            {
                "url": "https://github.com/repo/tax.py",
                "code": "def calculate_tax(amount: float) -> float:\n    return amount * 0.2",
                "summary": "Tax calculation helper",
                "metadata": {
                    "language": "python",
                    "framework": "fastapi",
                    "custom_flags": {"reviewed": True},
                },
                "source_id": "src_tax_repo",
                "similarity": 0.945,
                "rerank_score": 0.982,
                "extra_code_attribute": "preserved_unmapped_field",
            }
        ],
        "count": 1,
        "custom_pipeline_diagnostics": {"latency_ms": 42},
    }

    with patch("src.server.api_routes.knowledge.search.RAGService") as mock_rag_class:
        mock_instance = AsyncMock()
        mock_instance.search_code_examples_service = AsyncMock(return_value=(True, mock_code_search_result))
        mock_rag_class.return_value = mock_instance

        # MCP tool calls with source and match_count: {"query": "...", "source": "src_tax_repo", "match_count": 5}
        payload = {"query": "def calculate_tax", "source": "src_tax_repo", "match_count": 5}
        response = client.post("/api/rag/code-examples", json=payload)

        assert response.status_code == 200
        mock_instance.search_code_examples_service.assert_called_once_with(
            query="def calculate_tax", source_id="src_tax_repo", match_count=5
        )

        data = response.json()
        assert data["query"] == "def calculate_tax"
        assert data["source_filter"] == "src_tax_repo"
        assert data["search_mode"] == "hybrid"
        assert data["reranking_applied"] is True
        assert data["count"] == 1
        assert len(data["results"]) == 1

        item = data["results"][0]
        assert item["url"] == "https://github.com/repo/tax.py"
        assert "def calculate_tax" in item["code"]
        assert item["summary"] == "Tax calculation helper"
        assert item["metadata"]["language"] == "python"
        assert item["metadata"]["custom_flags"]["reviewed"] is True
        assert item["source_id"] == "src_tax_repo"
        assert item["similarity"] == 0.945
        assert item["rerank_score"] == 0.982
        assert item["extra_code_attribute"] == "preserved_unmapped_field"
        # Root-level extensible JSONB field survival
        assert data["custom_pipeline_diagnostics"]["latency_ms"] == 42


def test_search_code_examples_simple_contract(mock_user):
    """Verify that backward compatible /api/code-examples alias returns aligned CodeExamplesResponse."""
    mock_code_search_result = {
        "query": "async def fetch",
        "source_filter": "src_alias_repo",
        "search_mode": "vector",
        "reranking_applied": False,
        "results": [
            {
                "url": "https://github.com/repo/fetch.py",
                "code": "async def fetch(): pass",
                "summary": "Async fetcher",
                "metadata": {"tags": ["async"]},
                "source_id": "src_alias_repo",
                "similarity": 0.88,
            }
        ],
        "count": 1,
    }

    with patch("src.server.api_routes.knowledge.search.RAGService") as mock_rag_class:
        mock_instance = AsyncMock()
        mock_instance.search_code_examples_service = AsyncMock(return_value=(True, mock_code_search_result))
        mock_rag_class.return_value = mock_instance

        payload = {"query": "async def fetch", "source_ids": ["src_alias_repo"], "limit": 3}
        response = client.post("/api/code-examples", json=payload)

        assert response.status_code == 200
        mock_instance.search_code_examples_service.assert_called_once_with(
            query="async def fetch", source_id="src_alias_repo", match_count=3
        )

        data = response.json()
        assert data["query"] == "async def fetch"
        assert data["source_filter"] == "src_alias_repo"
        assert data["search_mode"] == "vector"
        assert data["reranking_applied"] is False
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["code"] == "async def fetch(): pass"
