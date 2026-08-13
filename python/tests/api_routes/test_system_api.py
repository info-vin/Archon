from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO


@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer test-admin-token"}

@pytest.fixture(autouse=True)
def override_dependency():
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(
        id="test-admin", role="system_admin", email="admin@archon.com"
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)

@pytest.mark.asyncio
async def test_fallback_status_success(auth_headers):
    # Mocking socket to succeed
    with patch("socket.socket.connect"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/system/fallback/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["internet_connected"] is True
        assert "active_tier" in data

@pytest.mark.asyncio
async def test_fallback_status_fail(auth_headers):
    # Mocking socket to throw an exception
    with patch("socket.socket.connect", side_effect=Exception("Connection failed")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/system/fallback/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["internet_connected"] is False
        assert "active_tier" in data
