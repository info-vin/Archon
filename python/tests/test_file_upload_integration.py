import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.api_routes.knowledge_api import _perform_upload_with_progress


# Mock dependencies for _perform_upload_with_progress
@pytest.fixture
def mock_dependencies():
    # Using parenthesized context managers for robustness
    with (patch("src.server.api_routes.knowledge_api.storage_service") as mock_storage_service,
          patch("src.server.api_routes.knowledge_api.DocumentStorageService") as MockDocumentStorageService,
          patch("src.server.api_routes.knowledge_api.ProgressTracker") as MockProgressTracker,
          patch("src.server.api_routes.knowledge_api.extract_text_from_document") as mock_extract_text,
          patch("src.server.api_routes.knowledge_api.get_supabase_client") as mock_get_supabase_client):

        # Mock storage_service.upload_file to be a proper async function
        mock_storage_service.upload_file = AsyncMock(return_value="http://mock.url/file.pdf")

        # Mock DocumentStorageService.upload_document to be a sync function that returns a tuple
        mock_doc_storage_instance = MockDocumentStorageService.return_value
        mock_doc_storage_instance.upload_document = AsyncMock(return_value=(True, {"chunks_stored": 10}))

        # Mock ProgressTracker
        mock_tracker_instance = MockProgressTracker.return_value
        mock_tracker_instance.start = AsyncMock()
        mock_tracker_instance.update = AsyncMock()
        mock_tracker_instance.error = AsyncMock()
        mock_tracker_instance.complete = AsyncMock()

        # Mock extract_text_from_document
        mock_extract_text.return_value = "mock extracted text"

        # Mock get_supabase_client to simulate a successful database write
        mock_supabase_client = MagicMock()
        # Configure the mock chain to return a response object with .error = None
        mock_response = MagicMock()
        mock_response.error = None
        mock_supabase_client.table.return_value.upsert.return_value.execute.return_value = mock_response
        mock_get_supabase_client.return_value = mock_supabase_client

        yield {
            "mock_storage_service": mock_storage_service,
            "MockDocumentStorageService": MockDocumentStorageService,
            "mock_doc_storage_instance": mock_doc_storage_instance,
            "MockProgressTracker": MockProgressTracker,
            "mock_tracker_instance": mock_tracker_instance,
            "mock_extract_text": mock_extract_text,
            "mock_get_supabase_client": mock_get_supabase_client,
            "mock_supabase_client": mock_supabase_client,
        }

@pytest.mark.asyncio
async def test_file_upload_runs_to_completion(mock_dependencies):
    """
    Test Verification: After all bugs are fixed, this test should run the code without error,
    asserting that the final payload is correct and the process completes.
    This test should PASS.
    """
    progress_id = str(uuid.uuid4())
    file_content = b"mock file content"
    file_metadata = {"filename": "test_final.pdf", "content_type": "application/pdf", "size": len(file_content)}
    tag_list = ["test", "final"]
    knowledge_type = "technical"
    tracker = mock_dependencies["mock_tracker_instance"]
    mock_supabase_client = mock_dependencies["mock_supabase_client"]

    # The real SourceManagementService will be instantiated, using the mocked supabase client.
    # The `create_source_from_upload` is now fully synchronous and correct.

    # Execute the background task
    await _perform_upload_with_progress(
        progress_id, file_content, file_metadata, tag_list, knowledge_type, tracker
    )

    # 1. Verify that no error was tracked
    tracker.error.assert_not_called()

    # 2. Verify the process completed successfully
    tracker.complete.assert_called_once()

    # 3. Verify that the 'upsert' method on the mocked Supabase client was called.
    mock_supabase_client.table.assert_called_with("archon_sources")
    upsert_call = mock_supabase_client.table.return_value.upsert
    upsert_call.assert_called_once()

    # 4. Inspect the payload and verify Bug B is fixed
    upserted_data = upsert_call.call_args[0][0]
    assert "source_display_name" in upserted_data
    assert upserted_data["source_display_name"] == file_metadata["filename"]
