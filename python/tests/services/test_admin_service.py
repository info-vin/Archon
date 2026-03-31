from unittest.mock import MagicMock, patch

import pytest

from src.server.services.admin_service import AdminService


@pytest.fixture
def mock_supabase():
    with patch("src.server.services.admin_service.get_supabase_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


@pytest.mark.asyncio
async def test_get_all_users(mock_supabase):
    # Mock response
    mock_response = MagicMock()
    mock_response.data = [{"id": "u1", "role": "admin"}, {"id": "u2", "role": "viewer"}]

    # Mock chain: table().select().order().limit().execute()
    mock_query = MagicMock()
    mock_supabase.table.return_value.select.return_value.order.return_value = mock_query
    mock_query.limit.return_value.execute.return_value = mock_response

    users = await AdminService.get_all_users(limit=10)

    assert len(users) == 2
    assert users[0]["role"] == "admin"
    mock_supabase.table.assert_called_with("profiles")


@pytest.mark.asyncio
async def test_update_user_role(mock_supabase):
    # Mock response
    mock_response = MagicMock()
    mock_response.data = [{"id": "u1", "role": "manager"}]

    # Mock chain: table().update().eq().execute()
    mock_update = MagicMock()
    mock_eq = MagicMock()

    mock_supabase.table.return_value.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_response

    result = await AdminService.update_user_role("u1", "manager", "admin@test.com")

    assert result["role"] == "manager"
    mock_supabase.table.assert_called_with("profiles")
    mock_supabase.table.return_value.update.assert_called_with({"role": "manager"})
