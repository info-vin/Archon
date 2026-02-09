
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# Create a minimal app for testing to avoid heavy imports from src.server.main
def create_test_app():
    # We need to import router AFTER patching services to avoid import side-effects
    # if those services are imported at module level in the router.
    # However, since we are patching at the test level, we rely on the patches being active
    # when the router is imported or functions are called.

    # In this case, we have to import the router, but we want to make sure
    # its dependencies are mocked.

    from src.server.api_routes.marketing_api import router
    app = FastAPI()
    app.include_router(router)
    return app

@pytest.fixture
def mock_dependencies():
    # Patch all the services used in marketing_api.py at module level or init
    with patch("src.server.api_routes.marketing_api.get_logger", return_value=MagicMock()), \
         patch("src.server.api_routes.marketing_api.TaskService") as mock_task_service, \
         patch("src.server.api_routes.marketing_api.RAGService"), \
         patch("src.server.api_routes.marketing_api.get_supabase_client"), \
         patch("src.server.api_routes.marketing_api.LogService"), \
         patch("src.server.api_routes.marketing_api.JobBoardService"), \
         patch("src.server.api_routes.marketing_api.get_llm_client"), \
         patch("src.server.api_routes.marketing_api.prompt_service"), \
         patch("src.server.api_routes.marketing_api.credential_service"):

        # Setup TaskService mock
        task_service_instance = mock_task_service.return_value
        task_service_instance.create_info_request_task = AsyncMock(return_value=(True, {"task": {"id": "task-123"}}))

        yield {
            "task_service": task_service_instance
        }

@pytest.fixture
def client(mock_dependencies):
    # Pass mock_dependencies fixture to ensure patches are active
    app = create_test_app()
    return TestClient(app)

def test_request_info_success(client, mock_dependencies):
    # We need to override the dependency get_current_user
    # But since we created a new app, we can override it on that app instance
    # However, client.app is the app

    from src.server.auth.dependencies import get_current_user
    client.app.dependency_overrides[get_current_user] = lambda: {"role": "marketing", "email": "bob@archon.com", "id": "user-bob"}

    payload = {
        "subject": "Missing Visit Logs",
        "context": "Need logs for Client X",
        "lead_id": "lead-001"
    }

    response = client.post("/api/marketing/request-info", json=payload)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["task"]["id"] == "task-123"

    # Verify Service Call
    mock_dependencies["task_service"].create_info_request_task.assert_called_once_with(
        requester_id="bob@archon.com",
        subject="Missing Visit Logs",
        context="Need logs for Client X",
        lead_id="lead-001"
    )

def test_request_info_forbidden(client, mock_dependencies):
    from src.server.auth.dependencies import get_current_user
    client.app.dependency_overrides[get_current_user] = lambda: {"role": "viewer", "email": "viewer@archon.com"}

    payload = {
        "subject": "Fail",
        "context": "Fail"
    }

    response = client.post("/api/marketing/request-info", json=payload)

    assert response.status_code == 403
