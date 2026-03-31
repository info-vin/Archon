from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.server.main import app

client = TestClient(app)

# Physical Note: The attendance module is not currently implemented in the backend router.
# We mark these tests as xfail until the business logic is physically added.


@pytest.fixture
def patch_api_dependencies():
    mock_supabase_client = MagicMock()
    with patch("src.server.utils.get_supabase_client", return_value=mock_supabase_client):
        yield mock_supabase_client


@pytest.mark.xfail(reason="Attendance API not physically implemented in the backend router yet.")
def test_attendance_clock_in_flow(patch_api_dependencies):
    resp = client.post("/api/attendance/clock-in", json={"user_id": "u1"})
    assert resp.status_code == 200


@pytest.mark.xfail(reason="Attendance API not physically implemented in the backend router yet.")
def test_attendance_double_clock_in(patch_api_dependencies):
    resp = client.post("/api/attendance/clock-in", json={"user_id": "u1"})
    assert resp.status_code == 400


@pytest.mark.xfail(reason="Attendance API not physically implemented in the backend router yet.")
def test_attendance_clock_out(patch_api_dependencies):
    resp = client.post("/api/attendance/clock-out", json={"user_id": "u1"})
    assert resp.status_code == 200


@pytest.mark.xfail(reason="Attendance API not physically implemented in the backend router yet.")
def test_get_attendance_status(patch_api_dependencies):
    resp = client.get("/api/attendance/status?user_id=u1")
    assert resp.status_code == 200
