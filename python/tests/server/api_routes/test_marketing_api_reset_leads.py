from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(id="test_user_id", role="admin", email="mock@archon.com")
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_reset_leads_endpoint_success(client):
    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.reset_leads = AsyncMock(return_value=True)

        response = client.post("/api/marketing/leads/reset")

        assert response.status_code == 200
        assert response.json() == {"success": True}
        mock_instance.reset_leads.assert_called_once()
