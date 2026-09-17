from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.server.main import app

client = TestClient(app)


def test_clear_ollama_cache_endpoint():
    response = client.delete("/api/ollama/cache")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "All Ollama caches cleared successfully"


def test_get_available_embedding_routes_endpoint():
    with patch(
        "src.server.api_routes.ollama.routing.embedding_router.get_available_embedding_routes",
        new_callable=AsyncMock,
    ) as mock_routes:
        mock_routes.return_value = []
        response = client.get("/api/ollama/embedding/routes?instance_urls=http://localhost:11434")
        assert response.status_code == 200
        data = response.json()
        assert data["total_routes"] == 0
        assert data["routes"] == []
        assert "dimension_analysis" in data
        assert "routing_statistics" in data
