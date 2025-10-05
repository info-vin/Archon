"""
Refactored integration tests to verify API response token optimization
in a proper pytest environment, using service-level mocking.
"""
import json
from unittest.mock import patch

# --- Mock Data ---

# A large content field to test the reduction for projects
MOCK_PROJECTS_DATA = [
    {
        "id": "proj-1",
        "name": "Project Alpha",
        "description": "A project about AI.",
        "content": "a" * 2000,  # This field should be excluded in the lightweight response
        "created_at": "2025-10-03T12:00:00Z",
    }
]

# A large description field to test the reduction for tasks
MOCK_TASKS_DATA = [
    {
        "id": "task-1",
        "title": "Analyze market trends",
        "project_id": "proj-1",
        "description": "b" * 1500,  # This field should be excluded/summarized
        "status": "in_progress",
    },
    {
        "id": "task-2",
        "title": "Draft report",
        "project_id": "proj-1",
        "description": "A short description.",
        "status": "todo",
    },
]

# A large content field to test the reduction for documents
MOCK_DOCS_DATA = [
    {
        "id": "doc-1",
        "name": "Research Paper.pdf",
        "project_id": "proj-1",
        "content": "c" * 3000,  # This field should be excluded
        "tags": ["research", "ai"],
    }
]


def measure_response_size(response):
    """Helper to get the byte size of a JSON response."""
    return len(json.dumps(response.json()))


@patch("src.server.api_routes.projects_api.SourceLinkingService")
@patch("src.server.api_routes.projects_api.ProjectService")
def test_projects_endpoint_optimization(mock_project_service, mock_source_service, client):
    """
    Tests that the /api/projects endpoint correctly reduces response size
    when requested.
    """
    # Arrange: Mock the ProjectService to return different data based on `include_content`.
    def list_projects_mock(include_content=True):
        if include_content:
            return (True, {"projects": MOCK_PROJECTS_DATA})
        else:
            # Return data without the large 'content' field
            light_data = [{k: v for k, v in MOCK_PROJECTS_DATA[0].items() if k != "content"}]
            return (True, {"projects": light_data})

    mock_project_service.return_value.list_projects.side_effect = list_projects_mock

    # Mock the SourceLinkingService to just pass through the data
    mock_source_service.return_value.format_projects_with_sources.side_effect = (
        lambda projects: projects
    )

    # Act & Measure: Test with full content (default behavior)
    response_full = client.get("/api/projects")
    assert response_full.status_code == 200
    projects_full = response_full.json()["projects"]
    size_full = len(json.dumps(projects_full))
    assert "content" in projects_full[0]

    # Act & Measure: Test lightweight (metadata only)
    response_light = client.get("/api/projects", params={"include_content": "false"})
    assert response_light.status_code == 200
    projects_light = response_light.json()["projects"]
    size_light = len(json.dumps(projects_light))
    assert "content" not in projects_light[0]

    # Assert: Check for significant reduction
    assert size_full > size_light
    reduction = (1 - size_light / size_full) * 100
    print(f"Projects Reduction: {reduction:.1f}%")
    assert reduction > 50


@patch("src.server.api_routes.projects_api.TaskService")
def test_tasks_endpoint_optimization(mock_task_service, client):
    """
    Tests that the /api/tasks endpoint correctly reduces response size
    by excluding large fields.
    """
    # Arrange: Mock the TaskService to return different data based on the flag.
    def list_tasks_mock(
        project_id=None,
        status=None,
        include_closed=False,
        exclude_large_fields=False,
        include_archived=False,
    ):
        if not exclude_large_fields:
            return (True, {"tasks": MOCK_TASKS_DATA})
        else:
            # In a real scenario, the service might summarize or remove fields.
            # Here, we simulate by removing the large description.
            light_data = []
            for task in MOCK_TASKS_DATA:
                new_task = task.copy()
                if len(new_task.get("description", "")) > 1000:
                    new_task["description"] = "..."  # Simulate field reduction
                light_data.append(new_task)
            return (True, {"tasks": light_data})

    mock_task_service.return_value.list_tasks.side_effect = list_tasks_mock

    # Act & Measure: Test with full content
    response_full = client.get("/api/tasks", params={"exclude_large_fields": "false"})
    assert response_full.status_code == 200
    tasks_full = response_full.json()["tasks"]
    size_full = len(json.dumps(tasks_full))
    assert len(tasks_full[0]["description"]) > 1000

    # Act & Measure: Test lightweight
    response_light = client.get("/api/tasks", params={"exclude_large_fields": "true"})
    assert response_light.status_code == 200
    tasks_light = response_light.json()["tasks"]
    size_light = len(json.dumps(tasks_light))
    assert len(tasks_light[0]["description"]) < 1000

    # Assert: Check for reduction
    assert size_full > size_light
    reduction = (1 - size_light / size_full) * 100
    print(f"Tasks Reduction: {reduction:.1f}%")
    assert reduction > 30


@patch("src.server.api_routes.projects_api.DocumentService")
def test_documents_endpoint_optimization(mock_document_service, client):
    """
    Tests that the /api/projects/{id}/docs endpoint correctly reduces response size.
    """
    project_id = "proj-1"

    # Arrange: Mock the DocumentService.
    def list_documents_mock(project_id, include_content=False):
        if include_content:
            return (True, {"documents": MOCK_DOCS_DATA, "total_count": len(MOCK_DOCS_DATA)})
        else:
            light_data = [{k: v for k, v in doc.items() if k != "content"} for doc in MOCK_DOCS_DATA]
            return (True, {"documents": light_data, "total_count": len(light_data)})

    mock_document_service.return_value.list_documents.side_effect = list_documents_mock

    # Act & Measure: Test with full content
    response_full = client.get(f"/api/projects/{project_id}/docs", params={"include_content": "true"})
    assert response_full.status_code == 200
    docs_full = response_full.json()["documents"]
    size_full = len(json.dumps(docs_full))
    assert "content" in docs_full[0]

    # Act & Measure: Test without content (default behavior for this endpoint)
    response_light = client.get(f"/api/projects/{project_id}/docs")
    assert response_light.status_code == 200
    docs_light = response_light.json()["documents"]
    size_light = len(json.dumps(docs_light))
    assert "content" not in docs_light[0]

    # Assert: Check for reduction
    assert size_full > size_light
    reduction = (1 - size_light / size_full) * 100
    print(f"Documents Reduction: {reduction:.1f}%")
    assert reduction > 80
