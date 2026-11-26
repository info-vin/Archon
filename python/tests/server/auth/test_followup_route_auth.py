"""Auth on the routes left open after the internal-token change.

Agent callbacks are MCP call_api paths, so a valid internal token is allowed.
/api/mcp-logs is not an MCP call_api path, so the same token stays forbidden.
These cases call the real get_current_user dependency. TestClient does not
raise server exceptions, so a BudgetGuard mishandled HTTPException shows up
as HTTP 500 instead of being swallowed.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from fastapi.testclient import TestClient

from server.auth.dependencies import get_current_user

TOKEN = "x3-internal-test-token"
HEADER = "X-Archon-Internal-Token"
_TEST_HMAC_KEY = "followup-auth-only"
STATUS_URL = "/api/tasks/task-1/agent-status"
OUTPUT_URL = "/api/tasks/task-1/agent-output"
LOGS_URL = "/api/mcp-logs"
STATUS_BODY = {"status": "doing", "agent_id": "agent-1"}
OUTPUT_BODY = {"output": {"summary": "done"}, "agent_id": "agent-1"}
CALLBACK_OK = {"task": {"id": "task-1", "status": "doing"}, "message": "ok"}


def _clear_user_override(app):
    saved = {
        dep: override
        for dep, override in app.dependency_overrides.items()
        if getattr(dep, "__name__", "") == "get_current_user"
    }
    for dep in saved:
        del app.dependency_overrides[dep]
    return saved


@pytest.fixture
def raw_app():
    import server.main as server_main

    server_main._initialization_complete = True
    app = server_main.app
    saved = _clear_user_override(app)
    assert get_current_user not in app.dependency_overrides
    yield app
    app.dependency_overrides.update(saved)


def _client(app) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _mint(claims: dict) -> str:
    token = jwt.encode(claims, _TEST_HMAC_KEY, algorithm="HS256")
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


def _assert_401(response):
    assert response.status_code == 401, f"status={response.status_code} body={response.text}"
    assert response.status_code != 500
    assert response.headers.get("www-authenticate", "").lower().startswith("bearer")


def _rejected_auth(mock_supabase_client):
    mock_supabase_client.auth.get_user.side_effect = RuntimeError("invalid session")
    return patch("server.auth.utils.get_supabase_client", return_value=mock_supabase_client)


def _accepted_user(mock_supabase_client, role: str = "system_admin"):
    user = SimpleNamespace(
        id="user-1",
        email="user@example.com",
        user_metadata={"role": role},
    )
    mock_supabase_client.auth.get_user.side_effect = None
    mock_supabase_client.auth.get_user.return_value = SimpleNamespace(user=user)
    return patch("server.auth.utils.get_supabase_client", return_value=mock_supabase_client)


def _with_profile(role: str):
    """Role comes from the profile row. user_metadata.role is not a privilege source."""
    return patch(
        "server.auth.dependencies.ProfileService.get_profile",
        return_value=(True, {"id": "user-1", "email": "user@example.com", "role": role}),
    )


def _callback_service(method_name: str):
    service = AsyncMock()
    setattr(service, method_name, AsyncMock(return_value=(True, CALLBACK_OK)))
    return patch("server.api_routes.projects.ops.TaskService", return_value=service)


@pytest.mark.parametrize("url,body", [(STATUS_URL, STATUS_BODY), (OUTPUT_URL, OUTPUT_BODY), (LOGS_URL, None)])
def test_missing_credentials_is_401(raw_app, url, body):
    client = _client(raw_app)
    response = client.post(url, json=body) if body is not None else client.get(url)
    _assert_401(response)


@pytest.mark.parametrize("url,body", [(STATUS_URL, STATUS_BODY), (OUTPUT_URL, OUTPUT_BODY), (LOGS_URL, None)])
def test_fake_bearer_is_401(raw_app, mock_supabase_client, url, body):
    with _rejected_auth(mock_supabase_client):
        client = _client(raw_app)
        headers = {"Authorization": "Bearer not-a-jwt"}
        response = (
            client.post(url, json=body, headers=headers) if body is not None else client.get(url, headers=headers)
        )
    _assert_401(response)


@pytest.mark.parametrize("url,body", [(STATUS_URL, STATUS_BODY), (OUTPUT_URL, OUTPUT_BODY), (LOGS_URL, None)])
def test_self_signed_bearer_is_401(raw_app, mock_supabase_client, url, body):
    token = _mint({"role": "service_role", "sub": str(uuid.uuid4())})
    with _rejected_auth(mock_supabase_client):
        client = _client(raw_app)
        headers = {"Authorization": f"Bearer {token}"}
        response = (
            client.post(url, json=body, headers=headers) if body is not None else client.get(url, headers=headers)
        )
    _assert_401(response)


def test_valid_user_can_report_agent_status(raw_app, mock_supabase_client):
    with _accepted_user(mock_supabase_client), _callback_service("update_task_status_from_agent"):
        response = _client(raw_app).post(
            STATUS_URL,
            json=STATUS_BODY,
            headers={"Authorization": "Bearer session-token"},
        )
    assert response.status_code == 200, response.text
    assert response.json()["task"]["id"] == "task-1"


def test_valid_user_can_report_agent_output(raw_app, mock_supabase_client):
    with _accepted_user(mock_supabase_client), _callback_service("save_agent_output"):
        response = _client(raw_app).post(
            OUTPUT_URL,
            json=OUTPUT_BODY,
            headers={"Authorization": "Bearer session-token"},
        )
    assert response.status_code == 200, response.text
    assert response.json()["task"]["id"] == "task-1"


def _read_mcp_logs(raw_app, mock_supabase_client, monkeypatch, tmp_path, role: str):
    missing = tmp_path / "missing-mcp.log"
    monkeypatch.setenv("ARCHON_MCP_LOG_PATH", str(missing))
    with _accepted_user(mock_supabase_client), _with_profile(role):
        return _client(raw_app).get(LOGS_URL, headers={"Authorization": "Bearer session-token"})


def test_mcp_logs_missing_credentials_is_401(raw_app):
    response = _client(raw_app).get(LOGS_URL)
    _assert_401(response)


def test_employee_cannot_read_mcp_logs(raw_app, mock_supabase_client, monkeypatch, tmp_path):
    response = _read_mcp_logs(raw_app, mock_supabase_client, monkeypatch, tmp_path, "employee")
    assert response.status_code == 403, response.text
    assert response.status_code != 500


def test_manager_cannot_read_mcp_logs(raw_app, mock_supabase_client, monkeypatch, tmp_path):
    response = _read_mcp_logs(raw_app, mock_supabase_client, monkeypatch, tmp_path, "manager")
    assert response.status_code == 403, response.text
    assert response.status_code != 500


def test_admin_can_read_mcp_logs(raw_app, mock_supabase_client, monkeypatch, tmp_path):
    response = _read_mcp_logs(raw_app, mock_supabase_client, monkeypatch, tmp_path, "admin")
    assert response.status_code == 200, response.text
    assert response.json()["error"] == "Log file not found"


def test_internal_token_can_report_agent_status(raw_app, monkeypatch):
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", TOKEN)
    with _callback_service("update_task_status_from_agent"):
        response = _client(raw_app).post(STATUS_URL, json=STATUS_BODY, headers={HEADER: TOKEN})
    assert response.status_code == 200, response.text


def test_internal_token_can_report_agent_output(raw_app, monkeypatch):
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", TOKEN)
    with _callback_service("save_agent_output"):
        response = _client(raw_app).post(OUTPUT_URL, json=OUTPUT_BODY, headers={HEADER: TOKEN})
    assert response.status_code == 200, response.text


def test_internal_token_cannot_read_mcp_logs(raw_app, monkeypatch, tmp_path):
    sentinel = tmp_path / "mcp.log"
    sentinel.write_text("SENTINEL_MCP_LOG", encoding="utf-8")
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", TOKEN)
    monkeypatch.setenv("ARCHON_MCP_LOG_PATH", str(sentinel))
    response = _client(raw_app).get(LOGS_URL, headers={HEADER: TOKEN})
    assert response.status_code == 403, response.text
    assert "SENTINEL_MCP_LOG" not in response.text
