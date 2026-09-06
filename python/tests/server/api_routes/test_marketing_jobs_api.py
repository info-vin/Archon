from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.main import app
from src.server.models.auth_models import UserProfileDTO
from src.server.services.crawling.clients.job104_client import JobData


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_user():
    return UserProfileDTO(
        id="00000000-0000-0000-0000-000000000001",
        email="test@example.com",
        role="marketing",
        department="marketing"
    )


def test_search_jobs_endpoint_success(client, mock_user):
    mock_jobs = [
        JobData(
            title="Python Developer",
            company="Tech Corp",
            location="Taipei",
            url="https://example.com/job/1",
            source="104"
        )
    ]

    with patch("src.server.api_routes.marketing_api.get_current_user", return_value=mock_user), \
         patch("src.server.services.marketing_service.MarketingService.search_jobs", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_jobs

        app.dependency_overrides[
            __import__("src.server.auth.dependencies", fromlist=["get_current_user"]).get_current_user
        ] = lambda: mock_user

        try:
            response = client.get("/api/marketing/jobs?keyword=python")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["title"] == "Python Developer"
            assert data[0]["company"] == "Tech Corp"
            assert data[0]["source"] == "104"
        finally:
            app.dependency_overrides.clear()
