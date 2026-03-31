from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def create_test_app():
    from src.server.api_routes.marketing_api import router

    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def mock_dependencies():
    with (
        patch("src.server.services.marketing_service.get_logger", return_value=MagicMock()),
        patch("src.server.services.marketing_service.RAGService") as mock_rag_class,
        patch("src.server.services.marketing_service.get_supabase_client") as mock_supabase_factory,
    ):
        mock_supabase = MagicMock()
        mock_supabase_factory.return_value = mock_supabase

        # Mock visit_logs fetch
        mock_logs_res = MagicMock()
        mock_logs_res.data = [{"summary": "Great meeting with Client X"}]
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_logs_res

        # Mock RAG Service
        mock_rag_instance = mock_rag_class.return_value
        mock_rag_instance.perform_rag_query = AsyncMock(return_value=(True, {"results": [{"content": "RAG Result 1"}]}))

        yield {"supabase": mock_supabase, "rag": mock_rag_instance}


@pytest.fixture
def client(mock_dependencies):
    app = create_test_app()
    return TestClient(app)


def test_get_context_success(client, mock_dependencies):
    from src.server.auth.dependencies import get_current_user

    # Inject Admin identity as requested
    client.app.dependency_overrides[get_current_user] = lambda: {
        "role": "admin",
        "email": "admin@archon.com",
        "id": "user-admin",
    }

    response = client.get("/api/marketing/context/lead-001")

    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "lead-001"
    assert "rag_refs" in data
    assert len(data["rag_refs"]) > 0
    assert "context_summary" in data
    assert "Great meeting" in data["context_summary"]


def test_get_context_unauthorized(client, mock_dependencies):
    # Mock get_current_user to raise 401 (unauthenticated)
    from fastapi import HTTPException

    from src.server.auth.dependencies import get_current_user

    def mock_get_current_user():
        raise HTTPException(status_code=401, detail="Unauthorized")

    client.app.dependency_overrides[get_current_user] = mock_get_current_user

    response = client.get("/api/marketing/context/lead-001")
    assert response.status_code == 401
