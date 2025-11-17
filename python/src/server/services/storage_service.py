
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

            supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=content,
                file_options={"content-type": content_type, "upsert": "true"}
            )

            # Deterministically construct the public URL instead of relying on get_public_url,
            # which can fail due to race conditions immediately after upload.
            # The format is: {SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_path}
            base_url = supabase.storage_url
            public_url = f"{base_url}/object/public/{bucket_name}/{file_path}"

            logger.info(f"Successfully uploaded file '{file.filename}' to bucket '{bucket_name}'. Public URL: {public_url}")
            return public_url

        except Exception as e:
            detailed_error_message = f"Storage upload failed: {e}"
            if hasattr(e, 'response') and e.response:
                try:
                    response_json = e.response.json()
                    detailed_error_message += f" Supabase response: {response_json}"
                except ValueError:
                    detailed_error_message += f" Supabase response text: {e.response.text}"
            logger.error(f"Failed to upload file to Supabase. Bucket: {bucket_name}, Error: {detailed_error_message}")
            raise StorageUploadError(detailed_error_message) from e

storage_service = StorageService()
