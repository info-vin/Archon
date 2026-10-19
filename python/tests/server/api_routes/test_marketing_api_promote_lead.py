import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


def mock_get_current_user():
    return UserProfileDTO(
        id=TEST_USER_ID,
        role="marketing",
        email="test@example.com",
    )


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


def test_promote_lead_success(client):
    fake_vendor = {
        "id": "11111111-1111-1111-1111-111111111111",
        "name": "ACME Vendor",
        "contact_email": "vendor@acme.com",
        "description": "Promoted from lead",
        "status": "active",
        "owner_id": TEST_USER_ID,
    }

    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.promote_to_vendor = AsyncMock(return_value=(True, {"vendor": fake_vendor}))

        response = client.post(
            "/api/marketing/leads/22222222-2222-2222-2222-222222222222/promote",
            json={
                "vendor_name": "ACME Vendor",
                "email": "vendor@acme.com",
                "notes": "Promoted from lead",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "vendor" in data
        assert data["vendor"]["id"] == "11111111-1111-1111-1111-111111111111"
        assert data["vendor"]["name"] == "ACME Vendor"
        assert data["vendor"]["contact_email"] == "vendor@acme.com"
        assert data["vendor"]["status"] == "active"
        mock_instance.promote_to_vendor.assert_awaited_once_with(
            "22222222-2222-2222-2222-222222222222",
            vendor_name="ACME Vendor",
            email="vendor@acme.com",
            notes="Promoted from lead",
            owner_id=TEST_USER_ID,
        )


def test_promote_lead_failure(client):
    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_class:
        mock_instance = mock_service_class.return_value
        mock_instance.promote_to_vendor = AsyncMock(return_value=(False, {"error": "Failed to create vendor"}))

        response = client.post(
            "/api/marketing/leads/22222222-2222-2222-2222-222222222222/promote",
            json={"vendor_name": "ACME Vendor"},
        )

        assert response.status_code == 400
        assert "Failed to create vendor" in response.json()["detail"]
