
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.server.services.storage_service import StorageUploadError

# This test uses the global 'client' fixture from conftest.py

@patch("src.server.api_routes.files_api.storage_service.upload_file", new_callable=AsyncMock)
def test_upload_file_success(mock_upload_file, client: TestClient):
    """Tests successful file upload API endpoint."""
    # Arrange
    mock_upload_file.return_value = "http://fake.url/success/test.pdf"
    
    file_content = b"this is a test file"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {"bucket_name": "test-bucket", "file_path": "test/test.pdf"}

    # Act
    response = client.post("/api/files/upload", files=files, data=data)

    # Assert
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["message"] == "File uploaded successfully"
    assert json_response["file_url"] == "http://fake.url/success/test.pdf"
    assert json_response["path"] == "test/test.pdf"
    mock_upload_file.assert_called_once()

@patch("src.server.api_routes.files_api.storage_service.upload_file", new_callable=AsyncMock)
def test_upload_file_storage_failure(mock_upload_file, client: TestClient):
    """Tests API response when the storage service fails."""
    # Arrange
    mock_upload_file.side_effect = StorageUploadError("Supabase connection failed")

    file_content = b"this is a test file"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    data = {"bucket_name": "test-bucket", "file_path": "test/test.pdf"}

    # Act
    response = client.post("/api/files/upload", files=files, data=data)

    # Assert
    assert response.status_code == 500
    json_response = response.json()
    assert "Failed to upload file" in json_response["detail"]
    assert "Supabase connection failed" in json_response["detail"]
    mock_upload_file.assert_called_once()

def test_upload_file_missing_data(client: TestClient):
    """Tests API response when form data is missing."""
    # Arrange
    file_content = b"this is a test file"
    files = {"file": ("test.pdf", file_content, "application/pdf")}
    # Missing bucket_name and file_path
    data = {}

    # Act
    response = client.post("/api/files/upload", files=files, data=data)

    # Assert
    assert response.status_code == 422 # Unprocessable Entity
    json_response = response.json()
    assert "Field required" in str(json_response["detail"])
