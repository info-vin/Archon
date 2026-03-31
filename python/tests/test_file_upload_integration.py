from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure server and src.server are both mock-friendly
from server.api_routes.knowledge.upload import background_upload


@pytest.fixture
def mock_supabase_client():
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_table.upsert.return_value.execute.return_value = MagicMock(data=[{"id": "test-source"}])
    mock_table.insert.return_value.execute.return_value = MagicMock(data=[{"id": "test-chunk"}])
    mock_client.table.return_value = mock_table
    return mock_client


@pytest.fixture
def mock_dependencies(mock_supabase_client):
    # DUAL PATH PATCHING: To prevent module shadowing errors (src.server vs server)
    patches = [
        # Patch both possible import paths for each dependency in upload.py
        patch("server.api_routes.knowledge.upload.SourceManagementService"),
        patch("src.server.api_routes.knowledge.upload.SourceManagementService"),
        patch("server.api_routes.knowledge.upload.DocumentStorageService"),
        patch("src.server.api_routes.knowledge.upload.DocumentStorageService"),
        patch("server.api_routes.knowledge.upload.ProgressTracker"),
        patch("src.server.api_routes.knowledge.upload.ProgressTracker"),
        patch("server.api_routes.knowledge.upload.extract_text_from_document", return_value="Test Content"),
        patch("src.server.api_routes.knowledge.upload.extract_text_from_document", return_value="Test Content"),
        patch("server.utils.get_supabase_client", return_value=mock_supabase_client),
        patch("src.server.utils.get_supabase_client", return_value=mock_supabase_client),
    ]

    # Start all patches and keep their mocks
    started_mocks = [p.start() for p in patches]

    # Configure Mocks (The first instances for SourceManager and StorageService)
    # Since we patch twice, we configure the common Mock instances
    mock_sm_inst = started_mocks[0].return_value  # server.api_routes...
    started_mocks[1].return_value = mock_sm_inst  # src.server.api_routes... (Link them)
    mock_sm_inst.create_source_info = AsyncMock(return_value=(True, {"id": "test-source"}))

    mock_storage_inst = started_mocks[2].return_value
    started_mocks[3].return_value = mock_storage_inst
    mock_storage_inst.store_documents = AsyncMock(return_value={"status": "success"})

    # Setup tracker (Link both patches to the same mock)
    mock_tracker_inst = MagicMock()
    mock_tracker_inst.start = AsyncMock()
    mock_tracker_inst.update = AsyncMock()
    mock_tracker_inst.complete = AsyncMock()
    started_mocks[4].return_value = mock_tracker_inst
    started_mocks[5].return_value = mock_tracker_inst

    yield {"tracker": mock_tracker_inst, "storage": mock_storage_inst, "source_manager": mock_sm_inst}

    # Cleanup
    for p in patches:
        p.stop()


@pytest.mark.asyncio
async def test_file_upload_runs_to_completion(mock_dependencies):
    tracker = mock_dependencies["tracker"]
    storage = mock_dependencies["storage"]
    source_manager = mock_dependencies["source_manager"]

    file_content = b"fake content"
    file_metadata = {"filename": "test.txt", "content_type": "text/plain"}
    tags = ["test"]
    knowledge_type = "technical"
    progress_id = "test-progress-id"

    # Execute the actual background logic
    await background_upload(
        file_content=file_content,
        file_metadata=file_metadata,
        progress_id=progress_id,
        tags=tags,
        knowledge_type=knowledge_type,
        tracker=tracker,
    )

    # Verify - Success state should be reached
    # We check if update and complete were called
    assert tracker.update.called
    assert tracker.complete.called

    # Crucially, ensure our MOCK source manager was the one called
    # (Checking .called on the mock instance we linked)
    assert source_manager.create_source_info.called
    assert storage.store_documents.called
