import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.server.main import app
from src.server.schemas.marketing import DraftFromLeadsRequest
from src.server.auth.dependencies import get_current_user

@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = lambda: {"id": "test_user_id", "role": "admin", "permissions": ["agent:trigger:mkt"]}
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


def test_draft_from_leads_success(client):
    with patch(
        "src.server.api_routes.marketing_api.MarketingService.draft_from_leads",
        new_callable=AsyncMock
    ) as mock_draft:
        mock_draft.return_value = (True, {"generated_count": 2, "drafts": [{"id": "1"}, {"id": "2"}]})
        
        response = client.post(
            "/api/marketing/draft-from-leads",
            json={"lead_ids": ["lead1", "lead2"]}
        )
        
        assert response.status_code == 200
        assert response.json() == {"generated_count": 2, "drafts": [{"id": "1"}, {"id": "2"}]}
        mock_draft.assert_called_once_with(["lead1", "lead2"])


def test_draft_from_leads_failure(client):
    with patch(
        "src.server.api_routes.marketing_api.MarketingService.draft_from_leads",
        new_callable=AsyncMock
    ) as mock_draft:
        mock_draft.return_value = (False, {"error_code": 404, "message": "No leads found for the provided IDs."})
        
        response = client.post(
            "/api/marketing/draft-from-leads",
            json={"lead_ids": ["invalid_lead"]}
        )
        
        assert response.status_code == 404
        assert response.json() == {"detail": "No leads found for the provided IDs."}
        mock_draft.assert_called_once_with(["invalid_lead"])

