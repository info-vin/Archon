from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO

client = TestClient(app)


@pytest.fixture
def mock_user():
    user = {"id": "user-uuid-1234", "role": "employee", "email": "user@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(**user) if isinstance(user, dict) else user
    yield user
    app.dependency_overrides = {}


@pytest.fixture
def mock_supabase():
    with patch("src.server.api_routes.game_api.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client


def test_save_game_success(mock_user, mock_supabase):
    # Arrange
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_upsert = MagicMock()
    mock_table.upsert.return_value = mock_upsert

    mock_result = MagicMock()
    mock_result.data = [{"user_id": "user-uuid-1234"}]
    mock_upsert.execute.return_value = mock_result

    # Act
    response = client.post("/api/game/save", json={"save_data": {"funds": 1000, "reputation": 95}})

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_supabase.table.assert_called_once_with("user_game_saves")
    mock_table.upsert.assert_called_once_with({
        "user_id": "user-uuid-1234",
        "save_data": {"funds": 1000, "reputation": 95},
        "updated_at": "now()"
    })


def test_save_game_database_error(mock_user, mock_supabase):
    # Arrange
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_upsert = MagicMock()
    mock_table.upsert.return_value = mock_upsert
    mock_upsert.execute.side_effect = Exception("DB Connection Down")

    # Act
    response = client.post("/api/game/save", json={"save_data": {"funds": 1000}})

    # Assert
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]


def test_load_game_success(mock_user, mock_supabase):
    # Arrange
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq

    mock_result = MagicMock()
    mock_result.data = [{"save_data": {"funds": 2500, "reputation": 88}}]
    mock_eq.execute.return_value = mock_result

    # Act
    response = client.get("/api/game/load")

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["save_data"]["funds"] == 2500
    mock_table.select.assert_called_once_with("save_data")
    mock_select.eq.assert_called_once_with("user_id", "user-uuid-1234")


def test_load_game_not_found(mock_user, mock_supabase):
    # Arrange
    mock_table = MagicMock()
    mock_supabase.table.return_value = mock_table
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq

    mock_result = MagicMock()
    mock_result.data = [] # No save game
    mock_eq.execute.return_value = mock_result

    # Act
    response = client.get("/api/game/load")

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"
    assert response.json()["save_data"] is None
