"""A request with no credentials must be 401, with WWW-Authenticate: Bearer.

The login route and an admin route are both checked. The client does not
override get_current_user.
"""

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


def _client():
    import server.main as server_main

    server_main._initialization_complete = True
    app = server_main.app
    saved = _clear_user_override(app)
    assert get_current_user not in app.dependency_overrides
    return TestClient(app, raise_server_exceptions=False), app, saved


def _assert_unauthorized(response):
    assert response.status_code == 401, f"status={response.status_code} body={response.text}"
    assert response.headers.get("www-authenticate", "").lower().startswith("bearer")


def test_login_route_without_credentials_is_401():
    client, app, saved = _client()
    try:
        response = client.get("/api/tasks")
    finally:
        app.dependency_overrides.update(saved)
    _assert_unauthorized(response)


def test_admin_route_without_credentials_is_401():
    client, app, saved = _client()
    try:
        response = client.get("/api/admin/david/read", params={"path": "pytest.ini"})
    finally:
        app.dependency_overrides.update(saved)
    _assert_unauthorized(response)
    assert "[pytest]" not in response.text
