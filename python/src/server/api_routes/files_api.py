
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from src.server.config.logfire_config import get_logger
from src.server.services.storage_service import StorageUploadError, storage_service

logger = get_logger(__name__)

router = APIRouter(prefix="/api/files", tags=["files"])

class FileUploadResponse(BaseModel):
    message: str
    file_url: str
    path: str

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(bucket_name: str = Form(...), file_path: str = Form(...), file: UploadFile = File(...)):
    """
    Uploads a file to a specified Supabase Storage bucket.

    Args:
        bucket_name: The destination bucket (e.g., 'attachments').
        file_path: The full path for the file within the bucket (e.g., 'project_x/report.pdf').
        file: The file to upload.

    Returns:
        A JSON response with the public URL of the uploaded file.
    """
    logger.info(f"Attempting to upload file '{file.filename}' to bucket '{bucket_name}'.")
    try:
        # Delegate the entire upload logic to the storage service
        public_url = await storage_service.upload_file(
            bucket_name=bucket_name,
            file_path=file_path,
            file=file
        )

        logger.info(f"File '{file.filename}' uploaded successfully.")
        return {
            "message": "File uploaded successfully",
            "file_url": public_url,
            "path": file_path
        }

    except StorageUploadError as e:
        logger.error(f"Storage service failed to upload file. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during file upload: {e}")
        raise HTTPException(status_code=500, detail="An unexpected error occurred.")
