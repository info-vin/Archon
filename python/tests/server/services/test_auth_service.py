from unittest.mock import MagicMock

import pytest

from src.server.services.auth_service import AuthService, UserProfileUpdateDTO


@pytest.fixture
def mock_supabase():
    client = MagicMock()
    # Mock admin auth client
    client.auth.admin = MagicMock()
    return client


@pytest.fixture
def auth_service(mock_supabase):
    return AuthService(supabase_client=mock_supabase)


def test_get_all_users_success(auth_service, mock_supabase):
    mock_supabase.table.return_value.select.return_value = MagicMock()
    auth_service.execute_query = MagicMock(
        return_value=(True, {"data": [{"id": "user-1", "name": "Alice", "email": "alice@example.com"}]})
    )

    users = auth_service.get_all_users()

    assert len(users) == 1
    assert users[0]["id"] == "user-1"
    assert users[0]["name"] == "Alice"
    auth_service.execute_query.assert_called_once()


def test_get_all_users_failure(auth_service, mock_supabase):
    mock_supabase.table.return_value.select.return_value = MagicMock()
    auth_service.execute_query = MagicMock(return_value=(False, {}))

    users = auth_service.get_all_users()

    assert users == []


def test_create_user_by_admin_success(auth_service, mock_supabase):
    mock_user = MagicMock()
    mock_user.id = "new-user-id"
    mock_supabase.auth.admin.create_user.return_value = MagicMock(user=mock_user)
    mock_supabase.table.return_value.upsert.return_value = MagicMock()
    auth_service.execute_query = MagicMock(return_value=(True, {}))

    res = auth_service.create_user_by_admin(
        email="test@example.com",
        password="secretpassword",
        name="Test User",
        role="admin",
        status="active",
    )

    assert res["id"] == "new-user-id"
    assert res["email"] == "test@example.com"
    assert res["name"] == "Test User"
    assert res["role"] == "admin"
    mock_supabase.auth.admin.create_user.assert_called_once_with(
        {
            "email": "test@example.com",
            "password": "secretpassword",
            "email_confirm": True,
            "user_metadata": {"name": "Test User", "role": "admin"},
        }
    )


def test_create_user_by_admin_auth_failed(auth_service, mock_supabase):
    mock_supabase.auth.admin.create_user.return_value = MagicMock(user=None)

    with pytest.raises(ValueError, match="Auth creation failed"):
        auth_service.create_user_by_admin(
            email="fail@example.com",
            password="secretpassword",
            name="Fail User",
        )


def test_register_user(auth_service):
    auth_service.create_user_by_admin = MagicMock(
        return_value={"id": "reg-id", "email": "reg@example.com", "name": "Reg", "role": "employee"}
    )

    res = auth_service.register_user("reg@example.com", "pass", "Reg")

    assert res["id"] == "reg-id"
    auth_service.create_user_by_admin.assert_called_once_with("reg@example.com", "pass", "Reg", "employee")


def test_update_user_email(auth_service, mock_supabase):
    mock_supabase.table.return_value.update.return_value.eq.return_value = MagicMock()
    auth_service.execute_query = MagicMock(return_value=(True, {}))

    auth_service.update_user_email("user-123", "newemail@example.com")

    mock_supabase.auth.admin.update_user_by_id.assert_called_once_with("user-123", {"email": "newemail@example.com"})
    auth_service.execute_query.assert_called_once()


def test_update_user_by_admin_success(auth_service, mock_supabase):
    mock_supabase.table.return_value.update.return_value.eq.return_value = MagicMock()
    updated_profile = {"id": "user-123", "name": "Updated Name", "role": "admin"}
    auth_service.execute_query = MagicMock(return_value=(True, {"data": [updated_profile]}))

    updates: UserProfileUpdateDTO = {"name": "Updated Name", "role": "admin"}
    res = auth_service.update_user_by_admin("user-123", updates)

    assert res["role"] == "admin"
    assert res["name"] == "Updated Name"
    mock_supabase.auth.admin.update_user_by_id.assert_called_once_with("user-123", {"user_metadata": {"role": "admin"}})


def test_update_user_by_admin_failure(auth_service, mock_supabase):
    mock_supabase.table.return_value.update.return_value.eq.return_value = MagicMock()
    auth_service.execute_query = MagicMock(return_value=(False, {}))

    updates: UserProfileUpdateDTO = {"name": "Updated Name"}
    with pytest.raises(ValueError, match="Failed to update profile for user-123"):
        auth_service.update_user_by_admin("user-123", updates)
