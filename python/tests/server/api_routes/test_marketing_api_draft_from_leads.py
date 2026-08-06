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


def test_draft_from_leads_success(client):
    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.draft_from_leads = AsyncMock(return_value=(True, {"task_id": "task123", "status": "dispatched"}))

        response = client.post(
            "/api/marketing/draft-from-leads",
            json={"lead_ids": ["lead1", "lead2"]}
        )

        assert response.status_code == 200
        assert response.json() == {"task_id": "task123", "status": "dispatched"}
        mock_instance.draft_from_leads.assert_called_once_with(["lead1", "lead2"])


def test_draft_from_leads_failure(client):
    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.draft_from_leads = AsyncMock(return_value=(False, {"error_code": 404, "message": "No leads found for the provided IDs."}))

        response = client.post(
            "/api/marketing/draft-from-leads",
            json={"lead_ids": ["invalid_lead"]}
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "No leads found for the provided IDs."}
        mock_instance.draft_from_leads.assert_called_once_with(["invalid_lead"])

