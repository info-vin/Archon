
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from src.server.services.storage_service import StorageService, StorageUploadError

# We need to patch the name as it is looked up in the storage_service module
@patch('src.server.services.storage_service.get_supabase_client')
@pytest.mark.asyncio
async def test_upload_file_success(mock_get_supabase_client):
    """Tests successful file upload with proper mocking."""
    # Arrange
    # Prepare a fake supabase instance and its chained calls
    mock_supabase_instance = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.upload = AsyncMock()
    mock_bucket.get_public_url.return_value = "http://fake.url/test.pdf"
    mock_supabase_instance.storage.from_.return_value = mock_bucket

    # Have the patched function return our fake instance
    mock_get_supabase_client.return_value = mock_supabase_instance

    service = StorageService()

    # Prepare a fake UploadFile object
    mock_file = MagicMock()
    mock_file.filename = "test.pdf"
    mock_file.read = AsyncMock(return_value=b"file content")

    # Act
    public_url = await service.upload_file("test-bucket", "test/test.pdf", mock_file)

    # Assert
    mock_get_supabase_client.assert_called_once()
    mock_supabase_instance.storage.from_.assert_called_with("test-bucket")
    mock_bucket.upload.assert_called_once()
    assert public_url == "http://fake.url/test.pdf"


@patch('src.server.services.storage_service.get_supabase_client')
@pytest.mark.asyncio
async def test_upload_file_failure(mock_get_supabase_client):
    """Tests file upload failure with proper mocking."""
    # Arrange
    mock_supabase_instance = MagicMock()
    mock_bucket = MagicMock()
    # Configure the upload method to raise an exception
    mock_bucket.upload = AsyncMock(side_effect=Exception("Supabase error"))
    mock_supabase_instance.storage.from_.return_value = mock_bucket

    mock_get_supabase_client.return_value = mock_supabase_instance

    service = StorageService()

    mock_file = MagicMock()
    mock_file.filename = "test.pdf"
    mock_file.read = AsyncMock(return_value=b"file content")

    # Act & Assert
    with pytest.raises(StorageUploadError, match="Supabase error"):
        await service.upload_file("test-bucket", "test/test.pdf", mock_file)

    mock_get_supabase_client.assert_called_once()
