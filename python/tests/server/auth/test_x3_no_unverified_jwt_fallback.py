"""X3: a bearer that Supabase auth.get_user does not accept must be 401.

The admin file route is the regression target. Tokens are minted inside the test
with a local HMAC key and are not credentials.
"""

import uuid
from types import SimpleNamespace
from unittest.mock import patch

import jwt
import pytest

DAVID_READ = "/api/admin/david/read"
PYTEST_INI = "pytest.ini"
_TEST_HMAC_KEY = "x3-regression-only"


def _pop_current_user_overrides(app):
    saved = {
        dep: override
        for dep, override in app.dependency_overrides.items()
        if getattr(dep, "__name__", "") == "get_current_user"
    }
    for dep in saved:
        del app.dependency_overrides[dep]
    return saved


@pytest.fixture
def raw_client(client):
    """Use the shared TestClient, but exercise the real get_current_user dependency."""
    saved = _pop_current_user_overrides(client.app)
    yield client
    client.app.dependency_overrides.update(saved)


def _mint_hs256(claims: dict) -> str:
    token = jwt.encode(claims, _TEST_HMAC_KEY, algorithm="HS256")
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _read(raw_client, mock_supabase_client, token: str):
    from unittest.mock import patch

    with patch("server.auth.utils.get_supabase_client", return_value=mock_supabase_client):
        return raw_client.get(DAVID_READ, params={"path": PYTEST_INI}, headers=_bearer(token))


def test_forged_service_role_jwt_cannot_read_admin_file(raw_client, mock_supabase_client):
    mock_supabase_client.auth.get_user.side_effect = RuntimeError("invalid session")
    token = _mint_hs256({"role": "service_role", "sub": str(uuid.uuid4())})

    response = _read(raw_client, mock_supabase_client, token)

    assert response.status_code == 401, f"status={response.status_code} pytest_ini_leaked={'[pytest]' in response.text}"


def test_verified_admin_user_can_read_admin_file(raw_client, mock_supabase_client):
    user = SimpleNamespace(
        id="admin-user",
        email="admin@example.com",
        user_metadata={},
    )
    mock_supabase_client.auth.get_user.side_effect = None
    mock_supabase_client.auth.get_user.return_value = SimpleNamespace(user=user)
    token = _mint_hs256({"role": "authenticated", "sub": user.id, "email": user.email})

    with patch("server.auth.dependencies.ProfileService") as mock_profile_svc:
        mock_profile_svc.return_value.get_profile.return_value = (
            True,
            {"id": "admin-user", "email": "admin@example.com", "role": "system_admin"},
        )
        response = _read(raw_client, mock_supabase_client, token)

    assert response.status_code == 200
    assert "[pytest]" in response.text


def test_user_metadata_role_cannot_escalate_to_admin(raw_client, mock_supabase_client):
    user = SimpleNamespace(
        id="attacker-user",
        email="attacker@example.com",
        user_metadata={"role": "system_admin"},
    )
    mock_supabase_client.auth.get_user.side_effect = None
    mock_supabase_client.auth.get_user.return_value = SimpleNamespace(user=user)
    token = _mint_hs256({"role": "authenticated", "sub": user.id, "email": user.email})

    with patch("server.auth.dependencies.ProfileService") as mock_profile_svc:
        mock_profile_svc.return_value.get_profile.return_value = (False, None)
        response = _read(raw_client, mock_supabase_client, token)

    assert response.status_code == 403


def test_get_user_exception_is_unauthorized(raw_client, mock_supabase_client):
    mock_supabase_client.auth.get_user.side_effect = RuntimeError("auth backend unavailable")

    response = _read(raw_client, mock_supabase_client, "not-a-jwt")

    assert response.status_code == 401
