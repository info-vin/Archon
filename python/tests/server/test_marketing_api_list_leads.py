import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
import uuid

from src.server.main import app
from src.server.auth.dependencies import get_current_user
from src.server.models.auth_models import UserProfileDTO

# Override dependency
def mock_get_current_user():
    return UserProfileDTO(id="test-user-id", role="admin", email="test@example.com")

app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(app)

def test_list_leads_success():
    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.list_leads = AsyncMock(return_value=[{"id": str(uuid.uuid4()), "company_name": "TestCorp", "status": "new"}])

        response = client.get("/api/marketing/leads")

        assert response.status_code == 200
        assert isinstance(response.json(), list)
        assert response.json()[0]["company_name"] == "TestCorp"
