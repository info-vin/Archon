"""
Reusable tool functions for file operations that can be wrapped by Agent tools.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any

# Use a forward reference for StorageService if it's not fully defined here
# This avoids circular import issues if services depend on each other.
from src.server.services.projects.task_service import TaskService
from src.server.services.storage_service import StorageService, StorageUploadError


async def upload_and_link_file_to_task(
    task_id: str,
    local_file_path: str,
    storage_service: StorageService,
    task_service: TaskService,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Uploads a file and links it to a specific task as an attachment.
    This is a helper function designed to be called by an Agent tool.

    Args:
        task_id: The ID of the task to link the file to.
        local_file_path: The local path of the file to upload.
        storage_service: An instance of the StorageService.
        task_service: An instance of the TaskService.
        description: An optional description for the attachment.

    Returns:
        A dictionary containing the result of the operation.
    """
    if not os.path.exists(local_file_path):
        return {"success": False, "error": f"File not found at {local_file_path}"}

    file_name = os.path.basename(local_file_path)
    bucket_name = "attachments"
    # Create a unique path in the bucket using the task_id to avoid collisions
    bucket_file_path = f"{task_id}/{file_name}"

    try:
        # 1. Upload the file using StorageService
        with open(local_file_path, "rb") as f:
            # The service expects an object with an async `read` method and a `filename` attribute.
            # We create a simple class that satisfies this interface for the service layer
            # without depending on a web framework like FastAPI.
            class SimpleUploadable:
                def __init__(self, file, filename):
                    self._file = file
                    self.filename = filename

                async def read(self) -> bytes:
                    return self._file.read()

            upload_file = SimpleUploadable(file=f, filename=file_name)
            public_url = await storage_service.upload_file(
                bucket_name=bucket_name,
                file_path=bucket_file_path,
                file=upload_file
            )

        # 2. Get the current task to safely update attachments
        success, result = await task_service.get_task(task_id)
        if not success:
            return {"success": False, "error": result.get("error", "Task not found")}

        task_data = result.get("task", {})
        current_attachments = task_data.get("attachments") or []

        # 3. Add the new attachment, ensuring no duplicates
        new_attachment = {
            "file_name": file_name,
            "url": public_url,
            "description": description or file_name,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
        # Avoid adding duplicate entries if the tool is run multiple times
        if new_attachment not in current_attachments:
            current_attachments.append(new_attachment)

        # 4. Update the task with the new attachments list
        update_fields = {"attachments": current_attachments}
        success, result = await task_service.update_task(task_id, update_fields)

        if not success:
            return {"success": False, "error": result.get("error", "Failed to update task")}

        return {"success": True, "message": f"Successfully uploaded and linked '{file_name}' to task {task_id}."}

    except StorageUploadError as e:
        return {"success": False, "error": f"Storage service error: {e}"}
    except Exception as e:
        return {"success": False, "error": f"An unexpected error occurred: {e}"}
