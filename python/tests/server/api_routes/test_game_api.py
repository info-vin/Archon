from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO

client = TestClient(app)

@pytest.fixture
def mock_user():
    user = {"id": "user-uuid-1234", "role": "employee", "email": "user@archon.com", "name": "Test User", "permissions": []}
    app.dependency_overrides[get_current_user] = lambda: UserProfileDTO(**user)
    yield user
    app.dependency_overrides = {}

@pytest.fixture
def mock_game_service():
    with patch("src.server.services.game_service.game_service") as mock_srv:
        mock_srv.save_game = AsyncMock()
        mock_srv.load_game = AsyncMock()
        yield mock_srv

def test_save_game_success(mock_user, mock_game_service):
    # Arrange
    mock_game_service.save_game.return_value = None

    # Act
    response = client.post("/api/game/save", json={"save_data": {"funds": 1000, "reputation": 95}})

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_game_service.save_game.assert_called_once_with(user_id="user-uuid-1234", save_data={"funds": 1000, "reputation": 95})

def test_save_game_database_error(mock_user, mock_game_service):
    # Arrange
    mock_game_service.save_game.side_effect = Exception("DB Connection Down")

    # Act
    response = client.post("/api/game/save", json={"save_data": {"funds": 1000}})

    # Assert
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]

def test_load_game_success(mock_user, mock_game_service):
    # Arrange
    mock_game_service.load_game.return_value = {"funds": 2500, "reputation": 88}

    # Act
    response = client.get("/api/game/load")

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["save_data"]["funds"] == 2500
    mock_game_service.load_game.assert_called_once_with(user_id="user-uuid-1234")

def test_load_game_not_found(mock_user, mock_game_service):
    # Arrange
    mock_game_service.load_game.return_value = None

    # Act
    response = client.get("/api/game/load")

    # Assert
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"
    assert response.json()["save_data"] is None
