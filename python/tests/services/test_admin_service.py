from unittest.mock import MagicMock, patch
import pytest
from src.server.services.admin_service import AdminService, admin_service

@pytest.fixture
def mock_execute_query():
    with patch("src.server.services.admin_service.admin_service.execute_query") as mock:
        yield mock

@pytest.fixture
def mock_supabase_client():
    with patch("src.server.services.admin_service.admin_service.supabase_client") as mock:
        yield mock

@pytest.mark.asyncio
async def test_get_all_users(mock_execute_query, mock_supabase_client):
    mock_execute_query.return_value = (True, {"data": [{"id": "u1", "role": "admin"}, {"id": "u2", "role": "viewer"}]})
    users = await admin_service.get_all_users(limit=10)
    assert len(users) == 2
    assert users[0]["role"] == "admin"
    assert mock_execute_query.called

@pytest.mark.asyncio
async def test_update_user_role(mock_execute_query, mock_supabase_client):
    def execute_side_effect(query, *args, **kwargs):
        if "update" in str(query):
            return (True, {"data": [{"id": "u1", "role": "manager"}]})
        return (True, {})
    mock_execute_query.side_effect = execute_side_effect
    mock_auth = MagicMock()
    mock_supabase_client.auth = mock_auth
    result = await admin_service.update_user_role("u1", "manager", "admin@test.com")
    assert result["role"] == "manager"
    assert mock_execute_query.called
