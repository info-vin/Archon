from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.auth.dependencies import get_current_user
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO

client = TestClient(app)


@pytest.fixture
def mock_admin_user():
    user = UserProfileDTO(id="admin1", role="admin", email="admin@archon.com", name="Admin")
    app.dependency_overrides[get_current_user] = lambda: user
    yield user
    app.dependency_overrides = {}


@pytest.fixture
def mock_versioning_service():
    with patch("src.server.api_routes.projects.versioning.VersioningService") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


def test_list_all_versions_success(mock_admin_user, mock_versioning_service):
    mock_versioning_service.list_all_versions.return_value = (
        True,
        {"versions": [{"id": "v1", "version_number": 1}], "total_count": 1},
    )

    response = client.get("/api/versions")

    assert response.status_code == 200
    assert response.json() == [{"id": "v1", "version_number": 1}]


def test_list_project_versions_success(mock_admin_user, mock_versioning_service):
    mock_versioning_service.list_versions.return_value = (
        True,
        {"versions": [{"id": "v1", "version_number": 1}], "total_count": 1},
    )

    response = client.get("/api/projects/p1/versions")

    assert response.status_code == 200
    assert response.json() == {"versions": [{"id": "v1", "version_number": 1}], "total_count": 1}


def test_create_project_version_success(mock_admin_user, mock_versioning_service):
    mock_versioning_service.create_version.return_value = (
        True,
        {"version": {"id": "v1", "field_name": "title", "version_number": 1}},
    )

    response = client.post(
        "/api/projects/p1/versions",
        json={"field_name": "title", "content": {"text": "v1"}},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Version created successfully",
        "version": {"id": "v1", "field_name": "title", "version_number": 1},
    }


def test_restore_project_version_success(mock_admin_user, mock_versioning_service):
    mock_versioning_service.restore_version.return_value = (
        True,
        {"restored_content": {"text": "restored"}},
    )

    response = client.post(
        "/api/projects/p1/versions/title/1/restore",
        json={"restored_by": "admin1"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Successfully restored title to version 1",
        "restored_content": {"text": "restored"},
    }
