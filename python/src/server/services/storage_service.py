
import mimetypes

from fastapi import UploadFile
from supabase import Client

from src.server.config.logfire_config import get_logger
from src.server.services.client_manager import get_supabase_client

logger = get_logger(__name__)

class StorageUploadError(Exception):
    """Custom exception for storage upload failures."""
    pass

class StorageService:
    def __init__(self):
        self._supabase: Client | None = None

    def _get_client(self) -> Client:
        """Lazily initializes and returns the Supabase client."""
        if self._supabase is None:
            self._supabase = get_supabase_client()
        return self._supabase

    async def upload_file(self, bucket_name: str, file_path: str, file: UploadFile) -> str:
        """
        Asynchronously uploads a file to the specified Supabase Storage bucket.
        """
        supabase = self._get_client()
        try:
            content = await file.read()
            content_type, _ = mimetypes.guess_type(file.filename)
            if content_type is None:
                content_type = "application/octet-stream"

            await supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=content,
                file_options={"content-type": content_type, "upsert": "true"}
            )

            public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)

            logger.info(f"Successfully uploaded file '{file.filename}' to bucket '{bucket_name}'.")
            return public_url

        except Exception as e:
            logger.error(f"Failed to upload file to Supabase. Bucket: {bucket_name}, Error: {e}")
            raise StorageUploadError(f"Storage upload failed: {e}") from e

storage_service = StorageService()
