"""MCP internal credential: compare_digest gate, no service-key fallback."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from server.auth.dependencies import get_current_user

TOKEN = "x3-internal-test-token"
HEADER = "X-Archon-Internal-Token"


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


def test_correct_internal_token_lists_tasks(raw_app, monkeypatch):
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", TOKEN)
    with patch(
        "server.api_routes.projects.ops.TaskService.list_tasks",
        new=AsyncMock(return_value=(True, {"tasks": []})),
    ):
        response = _client(raw_app).get("/api/tasks", headers={HEADER: TOKEN})

    assert response.status_code == 200, response.text
    assert response.json()["tasks"] == []


def test_correct_internal_token_can_query_rag(raw_app, monkeypatch):
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", TOKEN)
    with patch(
        "server.api_routes.knowledge.search.RAGService.perform_rag_query",
        new=AsyncMock(return_value=(True, {"results": [], "query": "auth", "success": True})),
    ):
        response = _client(raw_app).post(
            "/api/rag/query",
            json={"query": "auth"},
            headers={HEADER: TOKEN},
        )

    assert response.status_code == 200, response.text


def test_wrong_internal_token_is_rejected(raw_app, monkeypatch):
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", TOKEN)
    response = _client(raw_app).post(
        "/api/projects",
        json={"title": "nope"},
        headers={HEADER: "not-the-token"},
    )
    assert response.status_code == 401, response.text
    assert response.status_code != 500


def test_unset_internal_token_is_rejected(raw_app, monkeypatch):
    monkeypatch.delenv("ARCHON_INTERNAL_TOKEN", raising=False)
    response = _client(raw_app).get("/api/tasks", headers={HEADER: TOKEN})
    assert response.status_code == 401, response.text


def test_blank_internal_token_is_rejected(raw_app, monkeypatch):
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", "   ")
    response = _client(raw_app).get("/api/tasks", headers={HEADER: "   "})
    assert response.status_code == 401, response.text


def test_internal_actor_cannot_read_admin_file(raw_app, monkeypatch):
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", TOKEN)
    response = _client(raw_app).get(
        "/api/admin/david/read",
        params={"path": "pytest.ini"},
        headers={HEADER: TOKEN},
    )
    assert response.status_code == 403, response.text
    assert "[pytest]" not in response.text


def test_service_key_bearer_is_not_an_internal_credential(raw_app, monkeypatch, mock_supabase_client):
    monkeypatch.setenv("ARCHON_INTERNAL_TOKEN", TOKEN)
    mock_supabase_client.auth.get_user.side_effect = RuntimeError("not a user session")
    with patch("server.auth.utils.get_supabase_client", return_value=mock_supabase_client):
        response = _client(raw_app).get(
            "/api/tasks",
            headers={"Authorization": "Bearer test-key"},
        )
    assert response.status_code == 401, response.text
