"""
Simple tests for settings API credential handling.
Focus on critical paths for optional settings with defaults.
"""

from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.server.api_routes.settings_api import get_credential_service
from src.server.main import app


def test_optional_setting_returns_default(mock_supabase_client):
    """Test that optional settings return default values with is_default flag."""
    mock_credential_service = AsyncMock()
    mock_credential_service.get_credential.return_value = None
    app.dependency_overrides[get_credential_service] = lambda: mock_credential_service

    client = TestClient(app)
    response = client.get("/api/credentials/DISCONNECT_SCREEN_ENABLED")

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "DISCONNECT_SCREEN_ENABLED"
    assert data["value"] == "true"
    assert data["is_default"] is True
    assert "category" in data
    assert "description" in data

    # Clean up
    app.dependency_overrides = {}


def test_unknown_credential_returns_404(mock_supabase_client):
    """Test that unknown credentials still return 404."""
    mock_credential_service = AsyncMock()
    mock_credential_service.get_credential.return_value = None
    app.dependency_overrides[get_credential_service] = lambda: mock_credential_service

    client = TestClient(app)
    response = client.get("/api/credentials/UNKNOWN_KEY_THAT_DOES_NOT_EXIST")

    assert response.status_code == 404
    data = response.json()
    assert "error" in data["detail"]
    assert "not found" in data["detail"]["error"].lower()

    # Clean up
    app.dependency_overrides = {}


def test_existing_credential_returns_normally(mock_supabase_client):
    """Test that existing credentials return without default flag."""
    mock_value = "user_configured_value"
    mock_credential_service = AsyncMock()
    mock_credential_service.get_credential.return_value = mock_value
    app.dependency_overrides[get_credential_service] = lambda: mock_credential_service

    client = TestClient(app)
    response = client.get("/api/credentials/SOME_EXISTING_KEY")

    assert response.status_code == 200
    data = response.json()
    assert data["key"] == "SOME_EXISTING_KEY"
    assert data["value"] == "user_configured_value"
    assert data["is_encrypted"] is False
    # Should not have is_default flag for real credentials
    assert "is_default" not in data

    # Clean up
    app.dependency_overrides = {}
