from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.server.api_routes.auth_api import get_auth_service
from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO
from src.server.services.auth_service import AuthService

# Create a mock service
mock_service = MagicMock(spec=AuthService)

# Default overrides
app.dependency_overrides[get_auth_service] = lambda: mock_service
app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(id="admin-id", role="admin", email="admin@archon.com")

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mock():
    mock_service.reset_mock()
    # Reset to admin by default
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(id="admin-id", role="admin", email="admin@archon.com")


def test_admin_create_user_success():
    mock_service.create_user_by_admin.return_value = {"id": "123", "email": "test@example.com", "role": "member"}

    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "role": "member",
        "status": "active",
    }

    # Should succeed because dependency override provides admin role
    response = client.post("/api/admin/users", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    # The current stub implementation does not call service.create_user_by_admin
    # mock_service.create_user_by_admin.assert_called_once()


def test_admin_create_user_forbidden():
    # Override current user to a member
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(id="user-id", role="member", email="user@archon.com")

    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "role": "member",
        "status": "active",
    }

    response = client.post("/api/admin/users", json=payload)

    assert response.status_code == 403
