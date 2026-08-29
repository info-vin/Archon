from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.server.models.auth_models import UserProfileDTO
from src.server.services.propose_change_service import ProposedChangeDict


@pytest.fixture
def mock_user():
    return UserProfileDTO(
        id="user-123",
        email="test@example.com",
        role="admin",
        department="Engineering",
        permissions=["code:approve", "task:read_team"],
    )


@pytest.fixture
def mock_proposal() -> ProposedChangeDict:
    proposal_id = str(uuid4())
    return {
        "id": proposal_id,
        "created_at": "2025-01-01T00:00:00Z",
        "status": "pending",
        "type": "file",
        "request_payload": {
            "file_path": "test.txt",
            "old_content": "old",
            "new_content": "new",
            "created_by": "user-123",
            "created_by_dept": "Engineering",
            "change_summary": "Test summary",
        },
        "approved_by": None,
        "approved_at": None,
        "executed_at": None,
        "execution_log": None,
    }


def test_list_proposals(client: TestClient, mock_user: UserProfileDTO, mock_proposal: ProposedChangeDict):
    with (
        patch("src.server.api_routes.changes_api.get_current_user", return_value=mock_user),
        patch(
            "src.server.services.propose_change_service.ProposeChangeService.list_proposals",
            new_callable=AsyncMock,
            return_value=[mock_proposal],
        ),
    ):
        response = client.get("/api/changes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == mock_proposal["id"]
        assert data[0]["status"] == "pending"


def test_create_proposal(client: TestClient, mock_user: UserProfileDTO, mock_proposal: ProposedChangeDict):
    with (
        patch("src.server.api_routes.changes_api.get_current_user", return_value=mock_user),
        patch(
            "src.server.services.propose_change_service.ProposeChangeService.create_file_proposal",
            new_callable=AsyncMock,
            return_value=mock_proposal,
        ),
    ):
        payload = {"file_path": "test.txt", "new_content": "new content", "summary": "AI Fix"}
        response = client.post("/api/changes", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == mock_proposal["id"]
        assert data["request_payload"]["file_path"] == "test.txt"


def test_get_proposal(client: TestClient, mock_user: UserProfileDTO, mock_proposal: ProposedChangeDict):
    proposal_id = mock_proposal["id"]
    with (
        patch("src.server.api_routes.changes_api.get_current_user", return_value=mock_user),
        patch(
            "src.server.services.propose_change_service.ProposeChangeService.get_proposal",
            new_callable=AsyncMock,
            return_value=mock_proposal,
        ),
    ):
        response = client.get(f"/api/changes/{proposal_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == proposal_id


def test_approve_proposal(client: TestClient, mock_user: UserProfileDTO, mock_proposal: ProposedChangeDict):
    proposal_id = mock_proposal["id"]
    mock_proposal_approved = {**mock_proposal, "status": "approved", "approved_by": "user-123"}
    with (
        patch("src.server.api_routes.changes_api.requires_permission", lambda perm: lambda: mock_user),
        patch(
            "src.server.services.propose_change_service.ProposeChangeService.approve_proposal",
            new_callable=AsyncMock,
            return_value=mock_proposal_approved,
        ),
    ):
        response = client.post(f"/api/changes/{proposal_id}/approve")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Change approved and executed"
        assert data["details"]["status"] == "approved"


def test_reject_proposal(client: TestClient, mock_user: UserProfileDTO, mock_proposal: ProposedChangeDict):
    proposal_id = mock_proposal["id"]
    mock_proposal_rejected = {**mock_proposal, "status": "rejected", "approved_by": "user-123"}
    with (
        patch("src.server.api_routes.changes_api.requires_permission", lambda perm: lambda: mock_user),
        patch(
            "src.server.services.propose_change_service.ProposeChangeService.reject_proposal",
            new_callable=AsyncMock,
            return_value=mock_proposal_rejected,
        ),
    ):
        response = client.post(f"/api/changes/{proposal_id}/reject")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["message"] == "Change proposal rejected"
        assert data["details"]["status"] == "rejected"
