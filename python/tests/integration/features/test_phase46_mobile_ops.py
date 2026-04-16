from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app

client = TestClient(app)


@pytest.fixture
def mock_admin():
    user = {"id": "admin-id", "role": "system_admin", "department": "Sales"}
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides.pop(get_current_user, None)


def test_lead_lifecycle_mobile_ops(mock_admin):
    """驗證 Alice 在行動端的 Lead 完整生命週期"""
    # 1. Search Jobs (Physical Path: /api/marketing/jobs)
    with patch("src.server.api_routes.marketing_api.MarketingService.search_jobs") as mock_search:
        mock_search.return_value = []
        res = client.get("/api/marketing/jobs?keyword=AI")
        assert res.status_code == 200

    # 2. Create Lead
    with patch("src.server.api_routes.marketing_api.MarketingService.create_lead") as mock_create:
        mock_create.return_value = (True, {"lead": {"id": "l1"}})
        res = client.post("/api/marketing/leads", json={"company_name": "TestCorp"})
        assert res.status_code == 200


def test_visit_log_creation_no_audio(mock_admin):
    with patch("src.server.api_routes.visit_log_api.visit_log_service.create_log") as mock_create:
        mock_create.return_value = (True, {"id": "v1"})
        res = client.post("/api/visit-logs", json={"lead_id": "l1", "summary": "Visited"})
        assert res.status_code == 200


def test_visit_log_fetch_user(mock_admin):
    with patch("src.server.api_routes.visit_log_api.visit_log_service.list_logs") as mock_list:
        mock_list.return_value = (True, [])
        res = client.get("/api/visit-logs?lead_id=l1")
        assert res.status_code == 200
