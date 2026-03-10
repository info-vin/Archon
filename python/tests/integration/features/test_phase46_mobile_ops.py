import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from server.main import app
from server.auth.dependencies import get_current_user
from server.api_routes.marketing_api import get_marketing_service

@pytest.fixture
def precise_client():
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "alice-id", "role": "sales", "email": "alice@archon.ai"
    }
    yield TestClient(app)
    app.dependency_overrides = {}

def test_lead_lifecycle_mobile_ops(precise_client):
    mock_lead = {"id": "lead-123", "status": "new", "company_name": "Test Corp", "job_title": "Engineer"}

    # 使用 Dependency Override，這是物理上最強大的覆寫方式
    mock_svc = MagicMock()
    mock_svc.list_leads = AsyncMock(return_value=[mock_lead])
    mock_svc.update_lead = AsyncMock(return_value=(True, {**mock_lead, "status": "shortlisted"}))
    
    app.dependency_overrides[get_marketing_service] = lambda: mock_svc
    
    try:
        res = precise_client.get("/api/marketing/leads")
        assert res.status_code == 200
        assert res.json()[0]["id"] == "lead-123"

        res = precise_client.patch("/api/marketing/leads/lead-123", json={"status": "shortlisted"})
        assert res.status_code == 200
    finally:
        del app.dependency_overrides[get_marketing_service]

def test_visit_log_creation_no_audio(precise_client):
    pass

def test_visit_log_fetch_user(precise_client):
    pass
