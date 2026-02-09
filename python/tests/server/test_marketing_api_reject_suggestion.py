
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
    with patch("src.server.api_routes.marketing_api.get_logger", return_value=MagicMock()), \
         patch("src.server.api_routes.marketing_api.get_supabase_client") as mock_supabase, \
         patch("src.server.api_routes.marketing_api.credential_service") as mock_creds, \
         patch("src.server.api_routes.marketing_api.genai.Client") as mock_genai:

        # Mock Supabase
        mock_client = mock_supabase.return_value
        mock_table = MagicMock()
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_single = MagicMock()
        mock_execute = MagicMock()

        mock_client.table.return_value = mock_table
        mock_table.select.return_value = mock_select
        mock_select.eq.return_value = mock_eq
        mock_eq.single.return_value = mock_single
        mock_single.execute.return_value = mock_execute

        # Default: Post found
        mock_execute.data = {"title": "Bad Blog Post", "content": "This is bad content."}

        # Mock Credentials
        mock_creds.get_credential = AsyncMock(return_value="fake-api-key")

        # Mock GenAI
        mock_genai_instance = mock_genai.return_value
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a constructive rejection reason."
        mock_model.generate_content.return_value = mock_response
        mock_genai_instance.models = mock_model

        yield {
            "supabase": mock_execute,
            "genai": mock_genai_instance
        }

@pytest.fixture
def client(mock_dependencies):
    app = create_test_app()
    return TestClient(app)

def test_reject_suggestion_success(client, mock_dependencies):
    from src.server.auth.dependencies import get_current_user
    # Manager role
    client.app.dependency_overrides[get_current_user] = lambda: {"role": "manager", "email": "charlie@archon.com", "id": "user-charlie"}

    payload = {"blog_post_id": "post-123"}
    response = client.post("/api/marketing/approvals/reject-suggestion", json=payload)

    assert response.status_code == 200
    assert response.json()["suggested_reason"] == "This is a constructive rejection reason."

    # Verify GenAI call
    mock_dependencies["genai"].models.generate_content.assert_called_once()

def test_reject_suggestion_forbidden(client, mock_dependencies):
    from src.server.auth.dependencies import get_current_user
    # Marketing role (not allowed, only manager/admin)
    client.app.dependency_overrides[get_current_user] = lambda: {"role": "marketing", "email": "bob@archon.com"}

    payload = {"blog_post_id": "post-123"}
    response = client.post("/api/marketing/approvals/reject-suggestion", json=payload)

    assert response.status_code == 403

def test_reject_suggestion_not_found(client, mock_dependencies):
    from src.server.auth.dependencies import get_current_user
    client.app.dependency_overrides[get_current_user] = lambda: {"role": "manager", "email": "charlie@archon.com"}

    # Mock post not found
    mock_dependencies["supabase"].data = None

    payload = {"blog_post_id": "post-999"}
    response = client.post("/api/marketing/approvals/reject-suggestion", json=payload)

    assert response.status_code == 404
