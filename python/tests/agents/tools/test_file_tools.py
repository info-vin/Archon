"""
Unit tests for the file operation tool helpers.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.agents.tools.file_tools import upload_and_link_file_to_task
from src.server.services.projects.task_service import TaskService
from src.server.services.storage_service import StorageService

@pytest.mark.asyncio
async def test_upload_and_link_file_to_task_success(tmp_path, monkeypatch):
    """Test the successful execution of the upload_and_link_file_to_task helper function."""
    # 1. Setup
    task_id = "task-12345"
    local_file_name = "test_report.txt"
    local_file_path = tmp_path / local_file_name
    local_file_path.write_text("This is a test report.")
    description = "A test report for the agent tool."
    mock_public_url = f"https://fake-storage.com/attachments/{task_id}/{local_file_name}"

    # 2. Mock the service methods using monkeypatch
    mock_upload = AsyncMock(return_value=mock_public_url)
    mock_get_task = AsyncMock(return_value=(True, {"task": {"id": task_id, "attachments": []}}))
    mock_update_task = AsyncMock(return_value=(True, {"task": {"id": task_id}}))

    monkeypatch.setattr(StorageService, "upload_file", mock_upload)
    monkeypatch.setattr(TaskService, "get_task", mock_get_task)
    monkeypatch.setattr(TaskService, "update_task", mock_update_task)

    # 3. Instantiate the real services (their methods are now patched)
    storage_service = StorageService()
    task_service = TaskService()

    # 4. Execute the helper function
    result = await upload_and_link_file_to_task(
        task_id=task_id,
        local_file_path=str(local_file_path),
        storage_service=storage_service,
        task_service=task_service,
        description=description,
    )

    # 5. Assertions
    assert result["success"] is True
    assert "Successfully uploaded" in result["message"]

    # Assert that the mocked methods were called correctly
    mock_upload.assert_called_once()
    upload_args, upload_kwargs = mock_upload.call_args
    assert upload_kwargs['bucket_name'] == "attachments"
    assert upload_kwargs['file_path'] == f"{task_id}/{local_file_name}"

    mock_get_task.assert_called_once_with(task_id)
    mock_update_task.assert_called_once()
    
    update_args, update_kwargs = mock_update_task.call_args
    assert update_args[0] == task_id
    updated_attachments = update_args[1]['attachments']
    assert len(updated_attachments) == 1
    assert updated_attachments[0]["file_name"] == local_file_name
    assert updated_attachments[0]["url"] == mock_public_url
    assert updated_attachments[0]["description"] == description

@pytest.mark.asyncio
async def test_upload_file_not_found(tmp_path):
    """Test that the tool handles a non-existent local file."""
    # 1. Setup
    non_existent_path = str(tmp_path / "non_existent_file.txt")
    mock_storage_service = AsyncMock(spec=StorageService)
    mock_task_service = AsyncMock(spec=TaskService)

    # 2. Execute
    result = await upload_and_link_file_to_task(
        task_id="task-1",
        local_file_path=non_existent_path,
        storage_service=mock_storage_service,
        task_service=mock_task_service,
    )

    # 3. Assertions
    assert result["success"] is False
    assert "File not found" in result["error"]
    mock_storage_service.upload_file.assert_not_called()
    mock_task_service.update_task.assert_not_called()
