from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.server.api_routes.auth_api import get_auth_service
from src.server.main import app
from src.server.services.auth_service import AuthService

# Create a mock service
mock_service = MagicMock(spec=AuthService)

# Override the dependency
app.dependency_overrides[get_auth_service] = lambda: mock_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_mock():
    mock_service.reset_mock()

def test_admin_create_user_success():
    mock_service.create_user_by_admin.return_value = {
        "id": "123", "email": "test@example.com", "role": "member"
    }

    # Admin Header
    headers = {"X-User-Role": "system_admin"}
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "role": "member",
        "status": "active"
    }

    response = client.post("/api/admin/users", json=payload, headers=headers)

    assert response.status_code == 200
    assert response.json()["profile"]["email"] == "test@example.com"
    mock_service.create_user_by_admin.assert_called_once()

def test_admin_create_user_forbidden():
    headers = {"X-User-Role": "member"}
    payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "role": "member",
        "status": "active"
    }

    response = client.post("/api/admin/users", json=payload, headers=headers)

    assert response.status_code == 403

def test_register_user_success():
    mock_service.register_user.return_value = {
        "id": "123", "email": "new@example.com", "role": "member"
    }

    payload = {
        "name": "New User",
        "email": "new@example.com",
        "password": "password123"
    }

    response = client.post("/api/auth/register", json=payload)

    # Check if 400 is returned (maybe validation error?)
    if response.status_code != 200:
        print(response.json())

    assert response.status_code == 200
    mock_service.register_user.assert_called_once()
