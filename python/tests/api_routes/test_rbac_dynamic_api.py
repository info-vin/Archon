from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server.auth.dependencies import get_current_user
from server.main import app
from src.server.models.auth_models import UserProfileDTO

client = TestClient(app)

def mock_get_admin_user():
    return UserProfileDTO(id="test-admin-uuid", role="system_admin", email="admin@test.com")

@pytest.fixture
def admin_user():
    app.dependency_overrides[get_current_user] = mock_get_admin_user
    yield
    app.dependency_overrides.pop(get_current_user, None)

def test_get_rbac_matrix(admin_user):
    # Setup mock data for this test
    mock_data = [
        {"role": "system_admin", "permissions": ["*"]},
        {"role": "employee", "permissions": ["task:read"]}
    ]

    with patch("server.services.admin_service.get_supabase_client") as mock_get:
        mock_client = MagicMock()
        mock_get.return_value = mock_client
        mock_client.table.return_value.select.return_value.order.return_value.execute.return_value.data = mock_data

        response = client.get("/api/admin/rbac/matrix")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        roles = [r["role"] for r in data]
        assert "system_admin" in roles

def test_update_rbac_role(admin_user):
    # Setup mock data for updating
    with patch("server.services.admin_service.get_supabase_client") as mock_get:

        mock_client = MagicMock()
        mock_get.return_value = mock_client
        # Mock upsert response
        mock_client.table.return_value.upsert.return_value.execute.return_value.data = [
            {"role": "employee", "permissions": ["task:read", "dummy:perm"]}
        ]

        update_response = client.post("/api/admin/rbac/role", json={
            "role": "employee",
            "permissions": ["task:read", "dummy:perm"]
        })
        assert update_response.status_code == 200
        assert "dummy:perm" in update_response.json()["permissions"]
