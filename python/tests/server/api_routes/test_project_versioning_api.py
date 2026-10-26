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


def test_project_documents_preserves_jsonb_fields_and_string_version(mock_admin_user):
    with patch("src.server.api_routes.projects.core.DocumentService") as mock_doc_cls:
        doc_svc = MagicMock()
        mock_doc_cls.return_value = doc_svc
        doc_svc.list_documents.return_value = (
            True,
            {
                "documents": [
                    {
                        "id": "doc-1",
                        "title": "Architecture Spec",
                        "type": "spec",
                        "document_type": "spec",
                        "status": "draft",
                        "version": "1.0",
                        "stats": {"version_count": "1.0", "content_size": 512},
                        "custom_meta": "preserved",
                    }
                ]
            },
        )

        res = client.get("/api/projects/p1/docs")
        assert res.status_code == 200
        doc = res.json()["documents"][0]
        assert doc["document_type"] == "spec"
        assert doc["status"] == "draft"
        assert doc["version"] == "1.0"
        assert doc["stats"]["version_count"] == "1.0"
        assert doc["custom_meta"] == "preserved"


def test_create_project_document_returns_created_doc(mock_admin_user):
    mock_supabase = MagicMock()
    select_resp = MagicMock()
    select_resp.data = [{"docs": {}}]
    update_resp = MagicMock()
    update_resp.data = [{"id": "p1"}]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = select_resp
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = update_resp

    from src.server.services.projects.document_service import DocumentService

    real_svc = DocumentService(supabase_client=mock_supabase)
    with patch("src.server.api_routes.projects.core.DocumentService", return_value=real_svc):
        res = client.post(
            "/api/projects/p1/docs",
            json={"document_type": "spec", "title": "API Spec", "content": {"markdown": "# Spec"}},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["document"] is not None
        assert body["document"]["id"]
        assert body["document"]["document_type"] == "spec"
        assert body["document"]["type"] == "spec"


def test_get_task_preserves_agent_output_attachments_and_ai_metrics(mock_admin_user):
    from unittest.mock import AsyncMock

    with patch("src.server.api_routes.projects.ops.TaskService") as mock_task_cls:
        task_svc = MagicMock()
        mock_task_cls.return_value = task_svc
        task_svc.get_task = AsyncMock(
            return_value=(
                True,
                {
                    "task": {
                        "id": "task-1",
                        "project_id": "p1",
                        "title": "Daily Summary",
                        "status": "done",
                        "archived": False,
                        "attachments": [
                            {
                                "agent_id": "00000000-0000-0000-0000-000000000001",
                                "agent_name": "DevBot",
                                "status": "completed",
                                "output": {"summary": "All green"},
                                "timestamp": "2026-10-26T00:00:00Z",
                            }
                        ],
                        "agent_output": {"summary": "All green"},
                        "ai_metrics": {"total_tokens": 1200, "total_cost_usd": 0.0012, "is_ai_powered": True},
                        "stats": {"sources_count": 2, "code_examples_count": 1},
                    }
                },
            )
        )

        res = client.get("/api/tasks/task-1")
        assert res.status_code == 200
        data = res.json()
        assert data["agent_output"] == {"summary": "All green"}
        assert data["ai_metrics"]["total_tokens"] == 1200
        assert data["stats"]["sources_count"] == 2
        assert data["attachments"][0]["agent_name"] == "DevBot"
