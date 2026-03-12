import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from src.server.main import app
from src.server.auth.dependencies import get_current_user

client = TestClient(app)

@pytest.fixture
def mock_admin_user():
    user = {"id": "admin1", "role": "system_admin", "email": "admin@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)

@pytest.fixture
def mock_normal_user():
    user = {"id": "user1", "role": "employee", "email": "user@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)

def test_delete_knowledge_item_forbidden(mock_normal_user):
    """驗證普通員工無法刪除知識庫項目 (RBAC 403)"""
    # NO PATCH NEEDED: The dependency factory should block this physically
    response = client.delete("/api/knowledge-items/test-source-id")
    assert response.status_code == 403

def test_delete_knowledge_item_authorized(mock_admin_user):
    """驗證管理員可以刪除知識庫項目"""
    with patch("src.server.api_routes.knowledge.items.SourceManagementService.delete_source") as mock_delete:
        mock_delete.return_value = (True, {"id": "test-source-id"})
        response = client.delete("/api/knowledge-items/test-source-id")
        assert response.status_code == 200
        assert response.json()["success"] is True

def test_delete_knowledge_item_backward_compatibility(mock_admin_user):
    """驗證舊版路徑 alias 依然受控且可用"""
    with patch("src.server.api_routes.knowledge.items.SourceManagementService.delete_source") as mock_delete:
        mock_delete.return_value = (True, {"id": "test-source-id"})
        response = client.delete("/api/sources/test-source-id")
        assert response.status_code == 200
        assert response.json()["success"] is True
