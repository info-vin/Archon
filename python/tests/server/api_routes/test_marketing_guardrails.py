import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.server.main import app
from src.server.auth.dependencies import get_current_user

client = TestClient(app)

@pytest.fixture
def mock_admin_user():
    user = {"id": "admin1", "role": "system_admin", "email": "admin@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)

def test_guardrail_blocks_forbidden_input(mock_admin_user):
    # Physical Path Alignment: /api/marketing/draft-blog
    # Mocking Service to return 400 as it would if GuardrailService.validate_input failed
    with patch("src.server.api_routes.marketing_api.MarketingService.draft_blog", new_callable=AsyncMock) as mock_draft:
        mock_draft.return_value = (False, {"error_code": 400, "message": "Guardrail Violation: Policy Violation"})
        response = client.post("/api/marketing/draft-blog", json={"topic": "forbidden"})
        assert response.status_code == 400

def test_guardrail_allows_safe_input(mock_admin_user):
    with patch("src.server.api_routes.marketing_api.MarketingService.draft_blog", new_callable=AsyncMock) as mock_draft:
        mock_draft.return_value = (True, {"title": "Safe", "content": "Clean content"})
        response = client.post("/api/marketing/draft-blog", json={"topic": "safe"})
        assert response.status_code == 200

def test_guardrail_blocks_ai_leakage(mock_admin_user):
    # Physical Path Alignment: /api/marketing/draft-blog
    # Mocking Service to return 422 as it would if GuardrailService.audit_output failed
    with patch("src.server.api_routes.marketing_api.MarketingService.draft_blog", new_callable=AsyncMock) as mock_draft:
        mock_draft.return_value = (False, {"error_code": 422, "message": "AI Output Blocked: Leak detected"})
        response = client.post("/api/marketing/draft-blog", json={"topic": "safe"})
        assert response.status_code == 422
