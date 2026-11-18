"""Real supabase client construction checks.

tests/conftest.py replaces supabase.create_client with a MagicMock before any
test runs. These tests call supabase._sync.client.create_client, which that
patch does not replace, and stop before a successful network response.
"""

from postgrest._sync.request_builder import SyncQueryRequestBuilder
from supabase._sync.client import SupabaseException, create_client

from src.server.services import client_manager

# Split so the source does not contain a scannable key literal.
FAKE_SECRET_KEY = "sb_" + "secret" + "_not_a_real_key"
UNREACHABLE_URL = "http://127.0.0.1:9"


def _legacy_service_jwt() -> str:
    from jose import jwt

    return jwt.encode({"role": "service_role", "iss": "supabase"}, "secret", algorithm="HS256")


def _assert_surfaces(key: str) -> None:
    client = create_client(UNREACHABLE_URL, key)
    table_query = client.table("x").select("*")
    rpc_query = client.rpc("fn", {})
    bucket = client.storage.from_("b")
    functions = client.functions
    assert table_query is not None
    assert rpc_query is not None
    assert bucket is not None
    assert functions is not None


def test_real_client_constructs_surfaces_for_secret_and_legacy_jwt() -> None:
    """Builders are created for a fake secret key and a fake service-role JWT."""
    _assert_surfaces(FAKE_SECRET_KEY)
    _assert_surfaces(_legacy_service_jwt())


def test_execute_reaches_network_through_the_monkeypatch() -> None:
    """execute() is the patched builder method and fails on the closed port, not on key shape."""
    assert SyncQueryRequestBuilder.execute is client_manager._robust_execute
    client = create_client(UNREACHABLE_URL, FAKE_SECRET_KEY)
    try:
        client.table("x").select("*").execute()
    except (TypeError, SupabaseException) as exc:
        raise AssertionError(f"client construction or key check failed: {exc}") from exc
    except Exception as exc:
        message = str(exc).lower()
        assert "invalid api key" not in message
        # conftest's respx mock refuses hosts it does not know before a socket opens.
        # Outside that mock, the closed port raises a connection error. Both mean
        # execute() got past key checks and the request builder.
        assert any(
            token in message
            for token in ("connect", "connection", "refused", "network", "timed out", "timeout", "not mocked")
        )
    else:
        raise AssertionError("execute() returned without a transport error")
