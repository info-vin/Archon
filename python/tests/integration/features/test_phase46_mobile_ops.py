from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server.auth.dependencies import get_current_user

# Unit/Integration tests with precise patching to bypass conftest.py global mock pollution

@pytest.fixture
def precise_client():
    from server.main import app
    app.dependency_overrides[get_current_user] = lambda: {
        "id": "alice-id", "role": "sales", "email": "alice@archon.ai"
    }
    return TestClient(app)

@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    # Setup chain defaults to avoid iterating MagicMocks
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_insert = MagicMock()
    mock_update = MagicMock()

    mock.table.return_value = mock_table
    mock_table.select.return_value = mock_select
    mock_table.insert.return_value = mock_insert
    mock_table.update.return_value = mock_update

    # Chaining
    mock_select.eq.return_value = mock_select
    mock_select.order.return_value = mock_select
    mock_select.execute.return_value.data = []

    mock_update.eq.return_value = mock_update
    mock_update.execute.return_value.data = []

    mock_insert.execute.return_value.data = []

    return mock

@pytest.fixture
def mock_llm_client():
    mock_client_ctx = AsyncMock()
    mock_client = AsyncMock()
    mock_client_ctx.__aenter__.return_value = mock_client
    mock_client_ctx.__aexit__.return_value = None

    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"summary": "Mock Summary", "tasks": ["Task 1"]}'
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client_ctx

def test_lead_lifecycle_mobile_ops(precise_client, mock_supabase):
    mock_lead = {
        "id": "lead-123",
        "status": "new",
        "company_name": "Test Corp",
        "job_title": "Engineer"
    }

    # Patch MARKETING API import specifically
    with patch("server.api_routes.marketing_api.get_supabase_client", return_value=mock_supabase):

        # Configure Select
        mock_supabase.table.return_value.select.return_value.order.return_value.execute.return_value.data = [mock_lead]
        # Also simple select
        mock_supabase.table.return_value.select.return_value.execute.return_value.data = [mock_lead]

        res = precise_client.get("/api/marketing/leads")
        assert res.status_code == 200
        assert res.json()[0]["id"] == "lead-123"

        # Configure Update
        mock_update_chain = mock_supabase.table.return_value.update.return_value.eq.return_value
        mock_update_chain.execute.return_value.data = [{**mock_lead, "status": "shortlisted"}]

        res = precise_client.patch("/api/marketing/leads/lead-123", json={"status": "shortlisted"})
        assert res.status_code == 200


def test_visit_log_creation_no_audio(precise_client, mock_supabase):
    mock_visit = {
        "id": "visit-001",
        "user_id": "alice-id",
        "summary": "Mock Summary",
        "voice_transcript": "",
        "follow_up_tasks": []
    }

    # Patch VISIT LOG API import specifically
    with patch("server.api_routes.visit_log_api.get_supabase_client", return_value=mock_supabase):

        # Configure Insert
        # In visit_log_api: supabase.table("visit_logs").insert(log_data).execute()
        mock_insert_res = MagicMock()
        mock_insert_res.data = [mock_visit]

        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_res

        payload = {
            "customer_id": "",
            "latitude": "25.0330",
            "longitude": "121.5654",
            "location_address": "Taipei 101",
        }

        res = precise_client.post("/api/visit-logs/", data=payload)
        if res.status_code != 200:
            print(f"Error: {res.text}")
        assert res.status_code == 200
        assert res.json()["id"] == "visit-001"

def test_visit_log_fetch_user(precise_client, mock_supabase):
    mock_logs = [
        {"id": "v1", "user_id": "alice-id", "summary": "Visit 1", "created_at": "2025-01-01"},
        {"id": "v2", "user_id": "alice-id", "summary": "Visit 2", "created_at": "2025-01-02"}
    ]

    # Patch VISIT LOG API import
    with patch("server.api_routes.visit_log_api.get_supabase_client", return_value=mock_supabase):

        mock_res = MagicMock()
        mock_res.data = mock_logs

        # Select chain: select().eq().order().execute()
        mock_chain = mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value
        mock_chain.execute.return_value = mock_res

        res = precise_client.get("/api/visit-logs/user/alice-id")
        assert res.status_code == 200
        assert len(res.json()) == 2
