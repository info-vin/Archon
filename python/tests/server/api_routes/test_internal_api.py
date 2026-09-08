from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient

from src.server.main import app

client = TestClient(app)

def test_log_token_usage_success():
    with patch("src.server.services.token_usage_service.TokenUsageService.log_usage", new_callable=AsyncMock) as mock_log:
        response = client.post(
            "/internal/stats/token-usage",
            json={
                "model": "gpt-4o",
                "provider": "openai",
                "input_tokens": 100,
                "output_tokens": 50,
                "context_type": "test",
            },
            headers={"X-Internal-Key": "test_key"},
        )
        assert response.status_code == 200
        assert response.json() == {"success": True}

def test_get_agent_credentials_forbidden():
    with patch("src.server.api_routes.internal_api.is_internal_request", return_value=False):
        response = client.get("/internal/credentials/agents")
        assert response.status_code == 403

def test_get_agent_credentials_success():
    with patch("src.server.api_routes.internal_api.is_internal_request", return_value=True), \
         patch("src.server.services.credential_service.credential_service.get_credential", new_callable=AsyncMock) as mock_cred:
        mock_cred.return_value = "mock_val"
        response = client.get("/internal/credentials/agents", headers={"X-Internal-Key": "test_key"})
        assert response.status_code == 200
        data = response.json()
        assert "SUPERVISOR_AGENT_MODEL" in data
        assert "OPENAI_API_KEY" in data

def test_get_mcp_credentials_success():
    with patch("src.server.api_routes.internal_api.is_internal_request", return_value=True), \
         patch("src.server.services.credential_service.credential_service.get_credential", new_callable=AsyncMock) as mock_cred:
        mock_cred.return_value = "INFO"
        response = client.get("/internal/credentials/mcp", headers={"X-Internal-Key": "test_key"})
        assert response.status_code == 200
        assert response.json() == {"LOG_LEVEL": "INFO"}
