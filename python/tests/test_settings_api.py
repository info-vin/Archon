from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user, get_current_user_optional
from src.server.main import app

client = TestClient(app)


@pytest.fixture
def mock_admin_user():
    user = {"id": "admin1", "role": "system_admin", "email": "admin@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_current_user_optional] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_user_optional, None)


def test_optional_setting_returns_default(mock_admin_user):
    # Physical Path Alignment: /api/settings/credentials/...
    with patch("src.server.services.credential_service.CredentialService.get_credential") as mock_get:
        mock_get.return_value = "default-val"
        response = client.get("/api/credentials/NON_EXISTENT_KEY")
        assert response.status_code == 200
        assert response.json()["value"] == "default-val"


def test_unknown_credential_returns_404(mock_admin_user):
    with patch("src.server.services.credential_service.CredentialService.get_credential") as mock_get:
        mock_get.return_value = None
        response = client.get("/api/credentials/REALLY_UNKNOWN")
        assert response.status_code == 404


def test_existing_credential_returns_normally(mock_admin_user):
    with patch("src.server.services.credential_service.CredentialService.get_credential") as mock_get:
        mock_get.return_value = "secret-key"
        response = client.get("/api/credentials/GEMINI_API_KEY")
        assert response.status_code == 200
        assert response.json()["value"] == "secret-key"


def test_unauthenticated_public_setting_returns_default():
    # Should be accessible without mock_admin_user
    app.dependency_overrides.clear()
    with patch("src.server.services.credential_service.CredentialService.get_credential") as mock_get:
        mock_get.return_value = None
        response = client.get("/api/credentials/PROJECTS_ENABLED")
        assert response.status_code == 200
        assert response.json()["value"] == "true"  # From OPTIONAL_SETTINGS_WITH_DEFAULTS


def test_unauthenticated_private_setting_returns_401():
    # Should be rejected without mock_admin_user
    app.dependency_overrides.clear()
    with patch("src.server.services.credential_service.CredentialService.get_credential") as mock_get:
        mock_get.return_value = "secret-key"
        response = client.get("/api/credentials/GEMINI_API_KEY")
        assert response.status_code == 401
        assert "Authentication required" in str(response.json())
