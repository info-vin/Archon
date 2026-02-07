from unittest.mock import patch

import pytest

# Use the 'client' fixture from conftest.py which provides a TestClient
# and also the 'mock_supabase_client' fixture for setting up db mocks.

@pytest.fixture(autouse=True)
def patch_api_dependencies(mock_supabase_client):
    """Ensure the specific API module gets the mock client."""
    # Try patching BOTH paths to cover all bases
    with patch("server.api_routes.visit_log_api.get_supabase_client", return_value=mock_supabase_client):
        try:
            with patch("src.server.api_routes.visit_log_api.get_supabase_client", return_value=mock_supabase_client):
                yield
        except ImportError:
            # If src.server... fails to import (not in sys.modules), ignore it
            yield

def setup_mock_chain(mock_client):
    """Helper to setup the common Supabase chain mocks on the given client."""
    mock_select = mock_client.table.return_value.select.return_value

    # Ensure all chain methods return the same selector object
    mock_select.eq.return_value = mock_select
    mock_select.is_.return_value = mock_select
    mock_select.order.return_value = mock_select
    mock_select.limit.return_value = mock_select

    return mock_select

def test_attendance_clock_in_flow(client, mock_supabase_client):
    mock_select = setup_mock_chain(mock_supabase_client)

    # Mock: No existing active session (return empty list)
    mock_select.execute.return_value.data = []

    # Mock insert
    mock_supabase_client.table.return_value.insert.return_value.execute.return_value.data = [{"id": "log-123"}]

    resp = client.post("/api/visit-logs/attendance/clock-in", json={
        "latitude": 25.0, "longitude": 121.0, "location_name": "Test Loc", "status": "PRESENT"
    })
    assert resp.status_code == 200
    assert resp.json()["message"] == "Clocked in successfully"

def test_attendance_double_clock_in(client, mock_supabase_client):
    mock_select = setup_mock_chain(mock_supabase_client)

    # Mock: Existing active session found
    mock_select.execute.return_value.data = [{"id": "existing-123"}]

    resp = client.post("/api/visit-logs/attendance/clock-in", json={
        "latitude": 25.0, "longitude": 121.0, "location_name": "Duplicate", "status": "PRESENT"
    })
    assert resp.status_code == 400
    assert "Already clocked in" in resp.json()["detail"]

def test_attendance_clock_out(client, mock_supabase_client):
    mock_select = setup_mock_chain(mock_supabase_client)

    # Mock: Active session found
    # The code calls: .eq(...).is_(...).order(...).limit(1).execute()
    # Since we set all these to return mock_select, calling execute() on result of chain should return our data
    mock_select.execute.return_value.data = [{"id": "log-123"}]

    # Mock update
    mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{"id": "log-123"}]

    resp = client.post("/api/visit-logs/attendance/clock-out")
    assert resp.status_code == 200
    assert resp.json()["message"] == "Clocked out successfully"

def test_get_attendance_status(client, mock_supabase_client):
    mock_select = setup_mock_chain(mock_supabase_client)

    # Case 1: Clocked In
    mock_select.execute.return_value.data = [{
        "status": "PRESENT",
        "clock_in_time": "2023-10-27T09:00:00Z",
        "clock_out_time": None,
        "location_name": "Office"
    }]

    resp = client.get("/api/visit-logs/attendance/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "PRESENT"
    assert data["location"] == "Office"

    # Case 2: Clocked Out
    mock_select.execute.return_value.data = [{
        "status": "PRESENT",
        "clock_in_time": "2023-10-27T09:00:00Z",
        "clock_out_time": "2023-10-27T18:00:00Z"
    }]

    resp = client.get("/api/visit-logs/attendance/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "OFF_WORK"
