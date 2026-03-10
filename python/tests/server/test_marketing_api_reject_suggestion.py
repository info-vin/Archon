
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
    with patch("src.server.services.marketing_service.get_logger", return_value=MagicMock()), \
         patch("src.server.services.blog_service.BlogService.get_post") as mock_get_post, \
         patch("src.server.services.marketing_service.credential_service") as mock_creds, \
         patch("src.server.services.marketing_service.genai.Client") as mock_genai:

        # Default: Post found
        mock_get_post.return_value = (True, {"post": {"title": "Bad Blog Post", "content": "This is bad content."}})

        # Mock Credentials
        mock_creds.get_credential = AsyncMock(return_value="fake-api-key")
        mock_creds.get_active_provider = AsyncMock(return_value={"chat_model": "gemini-2.0-flash", "provider": "google"})

        # Mock GenAI
        mock_genai_instance = mock_genai.return_value
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a constructive rejection reason."
        mock_model.generate_content.return_value = mock_response
        mock_genai_instance.models = mock_model

        yield {
            "supabase": mock_get_post,
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

    # Mock BlogService.get_post to return failure
    mock_dependencies["supabase"].return_value = (False, {"error": "Not found"})

    payload = {"blog_post_id": "post-999"}
    response = client.post("/api/marketing/approvals/reject-suggestion", json=payload)

    assert response.status_code == 404
