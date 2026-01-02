from unittest.mock import patch

from fastapi.testclient import TestClient

from src.server.main import app

client = TestClient(app)

@patch('src.server.api_routes.knowledge_api.RBACService')
@patch('src.server.services.source_management_service.SourceManagementService')
def test_delete_knowledge_item_forbidden(MockSourceManagementService, MockRBACService):
    """Test that deleting a knowledge item with insufficient permissions returns 403."""
    # Setup RBAC to deny access
    rbac_instance = MockRBACService.return_value
    rbac_instance.can_manage_content.return_value = False

    # Mock Source Service (should not be called, but just in case)
    source_service_instance = MockSourceManagementService.return_value

    response = client.delete(
        "/api/knowledge-items/test-source-id",
        headers={"X-User-Role": "Member"}
    )

    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]

    # Verify RBAC was checked
    rbac_instance.can_manage_content.assert_called_with("Member")
    # Verify service was NOT called
    source_service_instance.delete_source.assert_not_called()

@patch('src.server.api_routes.knowledge_api.RBACService')
@patch('src.server.services.source_management_service.SourceManagementService')
def test_delete_knowledge_item_authorized(MockSourceManagementService, MockRBACService):
    """Test that deleting a knowledge item with correct permissions succeeds."""
    # Setup RBAC to allow access
    rbac_instance = MockRBACService.return_value
    rbac_instance.can_manage_content.return_value = True

    # Mock Source Service success
    source_service_instance = MockSourceManagementService.return_value
    source_service_instance.delete_source.return_value = (True, {})

    response = client.delete(
        "/api/knowledge-items/test-source-id",
        headers={"X-User-Role": "Admin"}
    )

    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify RBAC was checked
    rbac_instance.can_manage_content.assert_called_with("Admin")
    # Verify service WAS called
    source_service_instance.delete_source.assert_called_once()

@patch('src.server.api_routes.knowledge_api.RBACService')
@patch('src.server.services.source_management_service.SourceManagementService')
def test_delete_knowledge_item_backward_compatibility(MockSourceManagementService, MockRBACService):
    """Test that deleting without header is allowed (backward compatibility)."""

    # Mock Source Service success
    source_service_instance = MockSourceManagementService.return_value
    source_service_instance.delete_source.return_value = (True, {})

    # Call without headers
    response = client.delete("/api/knowledge-items/test-source-id")

    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify RBAC was NOT called (or at least logic skipped it)
    # Actually RBAC service might be instantiated but method not called if header is missing
    # But let's check that delete_source WAS called
    source_service_instance.delete_source.assert_called_once()
