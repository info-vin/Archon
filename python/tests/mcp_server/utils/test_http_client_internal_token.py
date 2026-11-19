"""call_api sends the internal header and never the Supabase service key."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp_server.utils.http_client import call_api


def _http_client(response: MagicMock) -> MagicMock:
    client = MagicMock()
    client.request = AsyncMock(return_value=response)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.mark.asyncio
async def test_call_api_sends_internal_header_not_service_key(monkeypatch):
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", "x3-internal-test-token")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key-must-not-be-a-bearer")
    response = MagicMock(status_code=200, text="")
    response.json.return_value = {"tasks": []}
    client = _http_client(response)

    with (
        patch("src.mcp_server.utils.http_client.get_api_url", return_value="http://archon-server:8181"),
        patch("src.mcp_server.utils.http_client.get_http_client") as get_client,
    ):
        get_client.return_value = client
        result = await call_api("GET", "/api/tasks")

    assert result["success"] is True
    _, kwargs = client.request.call_args
    headers = kwargs["headers"]
    assert headers["X-Archon-Internal-Token"] == "x3-internal-test-token"
    assert "Authorization" not in headers
    assert "service-key-must-not-be-a-bearer" not in str(headers)


@pytest.mark.asyncio
async def test_call_api_omits_header_when_token_unset(monkeypatch):
    monkeypatch.delenv("ARCHON_INTERNAL_TOKEN", raising=False)
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key-must-not-be-a-bearer")
    response = MagicMock(status_code=200, text="")
    response.json.return_value = {"ok": True}
    client = _http_client(response)

    with (
        patch("src.mcp_server.utils.http_client.get_api_url", return_value="http://archon-server:8181"),
        patch("src.mcp_server.utils.http_client.get_http_client") as get_client,
    ):
        get_client.return_value = client
        await call_api("POST", "/api/tasks/task-1/agent-status", json={"status": "doing", "agent_id": "a"})

    _, kwargs = client.request.call_args
    headers = kwargs["headers"]
    assert "X-Archon-Internal-Token" not in headers
    assert "Authorization" not in headers
