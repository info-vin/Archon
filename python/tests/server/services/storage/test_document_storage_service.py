from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Adjust import based on the actual location of the class
from src.server.services.storage.storage_services import DocumentStorageService


@pytest.mark.asyncio
async def test_upload_document_sets_source_type_file():
    """
    Test that upload_document explicitly sets 'source_type': 'file' in the metadata
    passed to add_documents_to_supabase.
    """

    # Mock dependencies
    with (
        patch(
            "src.server.services.storage.storage_services.add_documents_to_supabase", new_callable=AsyncMock
        ) as mock_add_docs,
        patch("src.server.services.storage.storage_services.get_logger"),
        patch("src.server.services.storage.storage_services.safe_span") as mock_safe_span,
    ):
        # Mock the context manager for safe_span
        mock_span_instance = MagicMock()
        mock_safe_span.return_value.__enter__.return_value = mock_span_instance

        # Initialize service with a mock supabase client
        mock_supabase = MagicMock()
        service = DocumentStorageService(supabase_client=mock_supabase)

        # Mock smart_chunk_text_async to return known chunks
        service.smart_chunk_text_async = AsyncMock(return_value=["chunk1", "chunk2"])

        # Call the method under test
        filename = "test_doc.pdf"
        source_id = "source_123"
        knowledge_type = "documentation"
        file_content = "This is some content."

        success, result = await service.upload_document(
            file_content=file_content, filename=filename, source_id=source_id, knowledge_type=knowledge_type
        )

        assert success is True

        # Verify add_documents_to_supabase was called
        mock_add_docs.assert_called_once()

        # Inspect arguments
        call_kwargs = mock_add_docs.call_args.kwargs
        metadatas = call_kwargs.get("metadatas")

        assert metadatas is not None
        assert len(metadatas) == 2

        # Check if source_type is set to 'file'
        for meta in metadatas:
            assert meta["source_type"] == "file"
            assert meta["filename"] == filename
            assert meta["knowledge_type"] == knowledge_type
