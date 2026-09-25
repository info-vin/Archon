import importlib
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture
def app():
    with patch("src.server.services.settings_service.SettingsService.get_setting", return_value="true"):
        import src.server.api_routes.test_api as test_api_module
        importlib.reload(test_api_module)

        test_app = FastAPI()
        test_app.include_router(test_api_module.router)
        yield test_app


@pytest.mark.asyncio
async def test_reset_database_endpoint(app):
    client = TestClient(app)
    with patch("src.server.api_routes.test_api.get_supabase_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.rpc.return_value.execute.return_value = None

        response = client.post("/api/test/reset-database")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Database reset and seeded successfully via API."


@pytest.mark.asyncio
async def test_trigger_agent_task_endpoint(app):
    client = TestClient(app)
    with patch("src.server.services.projects.task_service.task_service.get_task", new_callable=AsyncMock) as mock_get_task, \
         patch("src.server.services.projects.task_service.task_service.update_task", new_callable=AsyncMock), \
         patch("src.server.services.agent_service.agent_service.run_agent_task", new_callable=AsyncMock):

        mock_get_task.return_value = (True, {"task": {"description": "Existing description"}})

        payload = {
            "task_id": "task-123",
            "agent_id": "agent-456",
            "command": "do something"
        }
        response = client.post("/api/test/trigger-agent-task", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Task task-123 triggered for agent agent-456"
        assert data["command"] == "do something"
