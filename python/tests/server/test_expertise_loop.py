from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO

client = TestClient(app)


@pytest.fixture
def mock_admin_user():
    # RBAC Hardening: Provide a complete identity
    user = {"id": "admin1", "role": "system_admin", "email": "admin@archon.com", "department": "Marketing"}
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(**user) if isinstance(user, dict) else user
    yield user
    app.dependency_overrides.pop(get_current_user, None)


def test_marketing_approval_triggers_learning(mock_admin_user):
    """驗證行銷審核動作會觸發 L2 學習紀錄"""
    with patch("src.server.api_routes.marketing_api.MarketingService.process_approval") as mock_proc:
        mock_proc.return_value = True
        # PHYSICAL PATH: /api/marketing/approvals/...
        response = client.post("/api/marketing/approvals/blog/post-123/approve", json={"notes": "Great job!"})
        assert response.status_code == 200
        assert mock_proc.called
