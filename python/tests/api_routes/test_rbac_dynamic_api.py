from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from src.server.auth.dependencies import get_current_user
from src.server.main import app
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
    mock_data = [
        {"role": "system_admin", "permissions": ["*"]},
        {"role": "employee", "permissions": ["task:read"]}
    ]
    with patch("src.server.services.admin_service.admin_service.execute_query") as mock_eq:
        with patch("src.server.services.admin_service.admin_service.supabase_client"):
            mock_eq.return_value = (True, {"data": mock_data})
            response = client.get("/api/admin/rbac/matrix")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            roles = [r["role"] for r in data]
            assert "system_admin" in roles

def test_update_rbac_role(admin_user):
    with patch("src.server.services.admin_service.admin_service.execute_query") as mock_eq:
        with patch("src.server.services.admin_service.admin_service.supabase_client"):
            def execute_side_effect(query, *args, **kwargs):
                if "insert" in str(query) or "archon_logs" in str(query):
                    return (True, {})
                return (True, {"data": [{"role": "employee", "permissions": ["task:read", "dummy:perm"]}]})
            mock_eq.side_effect = execute_side_effect
            update_response = client.post("/api/admin/rbac/role", json={
                "role": "employee",
                "permissions": ["task:read", "dummy:perm"]
            })
            assert update_response.status_code == 200
            assert "dummy:perm" in update_response.json()["permissions"]
