
from unittest.mock import MagicMock, patch

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
         patch("src.server.services.marketing_service.LibrarianService.archive_style_critique") as mock_critique, \
         patch("src.server.services.marketing_service.credential_service"), \
         patch("src.server.services.marketing_service.get_supabase_client") as mock_supabase_factory:

        mock_supabase = MagicMock()
        mock_supabase_factory.return_value = mock_supabase

        # Mock successful update
        mock_res = MagicMock()
        mock_res.data = [{"id": "post-123", "title": "Bad Blog Post", "content": "This is bad content."}]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = mock_res

        yield {
            "supabase": mock_supabase,
            "mock_critique": mock_critique
        }

@pytest.fixture
def client(mock_dependencies):
    app = create_test_app()
    return TestClient(app)

def test_reject_suggestion_success(client, mock_dependencies):
    from src.server.auth.dependencies import get_current_user
    # Manager role has CONTENT_PUBLISH permission
    client.app.dependency_overrides[get_current_user] = lambda: {"role": "manager", "email": "charlie@archon.com", "id": "user-charlie"}

    payload = {"notes": "This is a constructive rejection reason."}
    response = client.post("/api/marketing/approvals/blog/post-123/reject", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is True

def test_reject_suggestion_forbidden(client, mock_dependencies):
    from src.server.auth.dependencies import get_current_user
    # Marketing role does NOT have CONTENT_PUBLISH permission
    client.app.dependency_overrides[get_current_user] = lambda: {"role": "marketing", "email": "bob@archon.com"}

    payload = {"notes": "Bad content"}
    response = client.post("/api/marketing/approvals/blog/post-123/reject", json=payload)

    assert response.status_code == 403

def test_reject_suggestion_invalid_type(client, mock_dependencies):
    from src.server.auth.dependencies import get_current_user
    client.app.dependency_overrides[get_current_user] = lambda: {"role": "manager", "email": "charlie@archon.com"}

    payload = {"notes": "Invalid type"}
    # item_type "unknown" should return success: False based on MarketingService logic
    response = client.post("/api/marketing/approvals/unknown/post-999/reject", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is False
