import pytest
from unittest.mock import patch, MagicMock
from src.server.models.auth_models import UserProfileDTO

@pytest.fixture
def mock_auth():
    with patch("src.server.auth.dependencies.get_current_user", return_value=UserProfileDTO(id="1", name="Test User", role="admin")):
        yield

@pytest.mark.asyncio
async def test_get_fallback_status(client, mock_auth):
    with patch("src.server.api_routes.system_api.requires_permission") as mock_perm:
        mock_perm.return_value = lambda: None
        with patch("src.server.services.credential_service.credential_service.get_active_tier", return_value=1):
            response = client.get("/api/system/fallback/status")
            assert response.status_code == 200
            data = response.json()
            assert "active_tier" in data
            assert data["active_tier"] == 1
            assert "internet_connected" in data
            assert isinstance(data["internet_connected"], bool)
