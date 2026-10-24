from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.auth.permissions import ALL_PERMISSIONS
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO


@pytest.fixture
def dummy_user():
    return UserProfileDTO(id="user-123", role="admin", email="test@archon.com")


@pytest.fixture
def client(dummy_user):
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    yield TestClient(app)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(autouse=True)
def mock_rbac_service():
    with patch("src.server.services.rbac_service.RBACService") as mock_rbac_cls:
        instance = mock_rbac_cls.return_value
        instance.get_role_permissions = AsyncMock(return_value=set(ALL_PERMISSIONS))
        yield mock_rbac_cls


def test_get_combined_sources_contract(client):
    mock_sources = [
        {
            "id": "src-1",
            "type": "lead",
            "title": "樸真國際股份有限公司",
            "score": 74,
            "summary": "工廠流程自動化 × 中台系統整合",
            "date": "2026-10-22T05:06:16Z",
        },
        {
            "id": "src-2",
            "type": "blog",
            "title": "AI 轉型爆發期",
            "score": 85,
            "summary": "企業 AI 導入案例",
            "date": "2026-10-20T03:00:00Z",
            "status": "draft",
        },
    ]

    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_cls:
        instance = mock_service_cls.return_value
        instance.get_combined_sources = AsyncMock(return_value=mock_sources)

        response = client.get("/api/marketing/sources")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["id"] == "src-1"
        assert data[0]["type"] == "lead"
        assert data[0]["title"] == "樸真國際股份有限公司"
        assert data[0]["score"] == 74
        assert data[0]["summary"] == "工廠流程自動化 × 中台系統整合"
        assert data[1]["status"] == "draft"


def test_get_manager_alerts_contract(client):
    mock_alerts = [
        {"id": "alert-1", "level": "ALERT", "source": "sentinel", "message": "High priority issue", "created_at": "2025-01-01T00:00:00Z", "details": {"score": 90}}
    ]

    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_cls:
        instance = mock_service_cls.return_value
        instance.get_manager_alerts = AsyncMock(return_value=mock_alerts)

        response = client.get("/api/marketing/manager/alerts")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "alert-1"
        assert data[0]["level"] == "ALERT"


def test_get_marketing_trends_contract(client):
    mock_trends = {
        "keyword_growth": [{"month": "2026-10", "AI Agent": 42, "RAG": 35}],
        "sankey_flow": {
            "nodes": [{"name": "104 爬蟲"}, {"name": "合格潛客"}],
            "links": [{"source": 0, "target": 1, "value": 12}],
        },
    }

    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_cls:
        instance = mock_service_cls.return_value
        instance.get_marketing_trends = AsyncMock(return_value=mock_trends)

        response = client.get("/api/marketing/trends")

        assert response.status_code == 200
        data = response.json()
        assert data["keyword_growth"] == [{"month": "2026-10", "AI Agent": 42, "RAG": 35}]
        assert data["sankey_flow"]["nodes"][0]["name"] == "104 爬蟲"


def test_get_marketing_intelligence_contract(client):
    mock_intel = {
        "total_leads": 100,
        "funnel": {"new": 50, "qualified": 30, "converted": 20},
        "distribution": {"AI/ML": 40, "Other": 60},
        "metrics": {"avg_conversion_hours": 12.5},
        "timestamp": "2025-01-01T00:00:00Z",
    }

    with patch("src.server.services.stats.metrics.MetricsManager") as mock_metrics_cls:
        instance = mock_metrics_cls.return_value
        instance.get_marketing_intelligence = AsyncMock(return_value=mock_intel)

        response = client.get("/api/marketing/intelligence")

        assert response.status_code == 200
        data = response.json()
        assert data["total_leads"] == 100
        assert data["funnel"]["new"] == 50
        assert data["metrics"]["avg_conversion_hours"] == 12.5


def test_seed_knowledge_base_contract(client):
    mock_res = {
        "status": "completed",
        "scanned_dir": "/app/frontend_public/aus/156_resource",
        "total_files": 12,
        "indexed_count": 10,
        "errors": [],
    }

    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_cls:
        instance = mock_service_cls.return_value
        instance.seed_knowledge = AsyncMock(return_value=mock_res)

        response = client.post("/api/marketing/knowledge/seed")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["scanned_dir"] == "/app/frontend_public/aus/156_resource"
        assert data["total_files"] == 12
        assert data["indexed_count"] == 10
        assert data["errors"] == []


def test_get_pending_approvals_contract(client):
    mock_approvals = {
        "blogs": [{"id": "post-1", "title": "AI Trends"}],
        "leads": [{"id": "lead-1", "company": "Tech Corp"}],
    }

    with patch("src.server.api_routes.marketing_api.MarketingService") as mock_service_cls:
        instance = mock_service_cls.return_value
        instance.get_pending_approvals = AsyncMock(return_value=mock_approvals)

        response = client.get("/api/marketing/approvals")

        assert response.status_code == 200
        data = response.json()
        assert len(data["blogs"]) == 1
        assert data["blogs"][0]["id"] == "post-1"
        assert len(data["leads"]) == 1
