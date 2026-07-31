from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Mock the database client completely so we don't need real DB connection during test loading
with patch('src.server.services.client_manager.get_supabase_client'):
    from src.server.main import app

client = TestClient(app)

class MockResponse:
    def __init__(self, status_code, text=""):
        self.status_code = status_code
        self.text = text

@pytest.fixture
def mock_httpx_get():
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        yield mock_get

@pytest.fixture
def mock_credential_service():
    with patch("src.server.api_routes.providers_api.credential_service.get_credential", new_callable=AsyncMock) as mock_get_cred:
        # Provide some dummy keys
        async def dummy_get_credential(key_name: str, *args, **kwargs):
            return f"dummy_{key_name}"
        mock_get_cred.side_effect = dummy_get_credential
        yield mock_get_cred

@pytest.mark.asyncio
async def test_provider_status_success(mock_httpx_get, mock_credential_service):
    """Test successful connectivity for various providers."""
    mock_httpx_get.return_value = MockResponse(status_code=200)

    # Test OpenAI
    response = client.get("/api/providers/openai/status")
    assert response.status_code == 200
    assert response.json() == {"ok": True, "reason": "connected", "provider": "openai"}

    # Verify the correct base URL was used
    mock_httpx_get.assert_called_with("https://api.openai.com/v1/models", headers={"Authorization": "Bearer dummy_OPENAI_API_KEY"})

    # Test Google
    response = client.get("/api/providers/google/status")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    # Assuming google maps to GEMINI_API_KEY
    mock_httpx_get.assert_called_with("https://generativelanguage.googleapis.com/v1beta/models", headers={"x-goog-api-key": "dummy_GEMINI_API_KEY"})

    # Test Anthropic
    response = client.get("/api/providers/anthropic/status")
    assert response.status_code == 200
    assert response.json()["ok"] is True
    mock_httpx_get.assert_called_with("https://api.anthropic.com/v1/models", headers={"x-api-key": "dummy_ANTHROPIC_API_KEY", "anthropic-version": "2023-06-01"})

@pytest.mark.asyncio
async def test_provider_status_failure(mock_httpx_get, mock_credential_service):
    """Test failed connectivity handling."""
    mock_httpx_get.return_value = MockResponse(status_code=401, text="Unauthorized")

    response = client.get("/api/providers/openai/status")
    assert response.status_code == 200
    assert response.json() == {"ok": False, "reason": "connection_failed", "provider": "openai"}

@pytest.mark.asyncio
async def test_provider_status_invalid_provider():
    """Test unsupported or invalid provider."""
    # Ollama is skipped
    response = client.get("/api/providers/ollama/status")
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]

    # Invalid provider
    response = client.get("/api/providers/invalid_fake/status")
    assert response.status_code == 400
    assert "Invalid provider" in response.json()["detail"]
