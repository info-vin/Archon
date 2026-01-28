
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app

client = TestClient(app)

@pytest.fixture
def mock_admin_user():
    user = {"id": "admin1", "role": "system_admin", "email": "admin@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides = {}

@pytest.fixture
def mock_user():
    user = {"id": "user1", "role": "member", "email": "user@archon.com"}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides = {}

@pytest.fixture
def mock_prompt_service():
    with patch("src.server.api_routes.prompts_api.prompt_service") as mock_service:
        yield mock_service

def test_list_prompts_admin_success(mock_admin_user, mock_prompt_service):
    # Arrange
    mock_prompt_service.list_prompts = AsyncMock(return_value=[
        {"prompt_name": "agent-1", "prompt": "Hello"}
    ])

    # Act
    response = client.get("/api/system/prompts")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["prompt_name"] == "agent-1"

def test_list_prompts_user_forbidden(mock_user, mock_prompt_service):
    # Act
    response = client.get("/api/system/prompts")

    # Assert
    assert response.status_code == 403

def test_update_prompt_admin_success(mock_admin_user, mock_prompt_service):
    # Arrange
    mock_prompt_service.update_prompt = AsyncMock(return_value=(True, "Updated"))

    # Act
    response = client.patch("/api/system/prompts/agent-1", json={
        "content": "New Prompt",
        "description": "New Desc"
    })

    # Assert
    assert response.status_code == 200
    mock_prompt_service.update_prompt.assert_called_once_with(
        prompt_name="agent-1",
        content="New Prompt",
        description="New Desc"
    )

def test_update_prompt_admin_failure(mock_admin_user, mock_prompt_service):
    # Arrange
    mock_prompt_service.update_prompt = AsyncMock(return_value=(False, "DB Error"))

    # Act
    response = client.patch("/api/system/prompts/agent-1", json={
        "content": "New Prompt"
    })

    # Assert
    assert response.status_code == 500
    assert response.json()["detail"] == "DB Error"
