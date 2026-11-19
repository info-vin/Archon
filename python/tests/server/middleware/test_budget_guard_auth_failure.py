"""BudgetGuard must not turn an auth failure into HTTP 500.

BaseHTTPMiddleware does not route HTTPException through FastAPI's
ExceptionMiddleware. A raised 401 is handled by the global handler as 500.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from server.auth.dependencies import get_current_user


def _clear_user_override(app):
    saved = {
        dep: override
        for dep, override in app.dependency_overrides.items()
        if getattr(dep, "__name__", "") == "get_current_user"
    }
    for dep in saved:
        del app.dependency_overrides[dep]
    return saved


def _client(mock_supabase_client):
    import server.main as server_main

    server_main._initialization_complete = True
    app = server_main.app
    saved = _clear_user_override(app)
    assert get_current_user not in app.dependency_overrides
    probe = TestClient(app, raise_server_exceptions=False)
    return probe, app, saved


def test_invalid_bearer_on_post_is_401_not_500(mock_supabase_client):
    mock_supabase_client.auth.get_user.side_effect = RuntimeError("invalid session")
    with patch("server.auth.utils.get_supabase_client", return_value=mock_supabase_client):
        client, app, saved = _client(mock_supabase_client)
        try:
            response = client.post(
                "/api/projects",
                json={"title": "budget-guard-probe"},
                headers={"Authorization": "Bearer not-a-jwt"},
            )
        finally:
            app.dependency_overrides.update(saved)

    assert response.status_code == 401, f"status={response.status_code} body={response.text}"
    assert response.status_code != 500


def test_valid_bearer_on_post_is_not_rejected(mock_supabase_client):
    user = SimpleNamespace(
        id="admin-user",
        email="admin@example.com",
        user_metadata={"role": "system_admin"},
    )
    mock_supabase_client.auth.get_user.side_effect = None
    mock_supabase_client.auth.get_user.return_value = SimpleNamespace(user=user)
    created = {"project_id": "p-budget", "project": {"id": "p-budget", "title": "budget-guard-probe"}}
    with (
        patch("server.auth.utils.get_supabase_client", return_value=mock_supabase_client),
        patch(
            "server.api_routes.projects.core.ProjectCreationService.create_project_with_ai",
            new=AsyncMock(return_value=(True, created)),
        ),
    ):
        client, app, saved = _client(mock_supabase_client)
        try:
            response = client.post(
                "/api/projects",
                json={"title": "budget-guard-probe"},
                headers={"Authorization": "Bearer session-token"},
            )
        finally:
            app.dependency_overrides.update(saved)

    assert response.status_code not in (401, 500), f"status={response.status_code} body={response.text}"
