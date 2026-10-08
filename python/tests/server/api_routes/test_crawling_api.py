import pytest
from fastapi.testclient import TestClient

from src.server.main import app
from src.server.utils.progress import ProgressTracker

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_progress_states():
    """Clear progress states before and after tests."""
    ProgressTracker._progress_states.clear()
    yield
    ProgressTracker._progress_states.clear()


def test_get_crawl_progress_success():
    """Verify getting crawl progress returns 200 with structured response model."""
    progress_id = "test-crawl-progress-123"
    tracker = ProgressTracker(progress_id, operation_type="crawl")
    tracker.state.update(
        {
            "status": "crawling",
            "progress": 50,
            "log": "Crawling page 1",
            "processed_pages": 1,
            "total_pages": 2,
        }
    )

    response = client.get(f"/api/crawl-progress/{progress_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["progressId"] == progress_id
    assert data["status"] == "crawling"
    assert data["progress"] == 50.0
    assert data["message"] == "Crawling page 1"


def test_get_crawl_progress_not_found():
    """Verify getting non-existent crawl progress returns 404."""
    response = client.get("/api/crawl-progress/non-existent-id")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"] == "Progress ID not found"
