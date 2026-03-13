from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app

client = TestClient(app)

@pytest.fixture
def mock_admin_user():
    user = {"id": "admin1", "role": "system_admin", "email": "admin@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)

def test_optional_setting_returns_default(mock_admin_user):
    # Physical Path Alignment: /api/settings/credentials/...
    with patch("src.server.services.credential_service.CredentialService.get_credential") as mock_get:
        mock_get.return_value = "default-val"
        response = client.get("/api/settings/credentials/NON_EXISTENT_KEY")
        assert response.status_code == 200
        assert response.json()["value"] == "default-val"

def test_unknown_credential_returns_404(mock_admin_user):
    with patch("src.server.services.credential_service.CredentialService.get_credential") as mock_get:
        mock_get.return_value = None
        response = client.get("/api/settings/credentials/REALLY_UNKNOWN")
        assert response.status_code == 404

def test_existing_credential_returns_normally(mock_admin_user):
    with patch("src.server.services.credential_service.CredentialService.get_credential") as mock_get:
        mock_get.return_value = "secret-key"
        response = client.get("/api/settings/credentials/GEMINI_API_KEY")
        assert response.status_code == 200
        assert response.json()["value"] == "secret-key"
