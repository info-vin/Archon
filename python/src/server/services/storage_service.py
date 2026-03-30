
import mimetypes
from typing import cast

from fastapi import UploadFile
from supabase import Client

from src.server.config.logfire_config import get_logger
from src.server.services.client_manager import get_supabase_client

logger = get_logger(__name__)

class StorageUploadError(Exception):
    """Custom exception for storage upload failures with HTTP-aligned status codes."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

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
            filename = file.filename or "unknown"
            content_type, _ = mimetypes.guess_type(filename)
            if content_type is None:
                content_type = "application/octet-stream"

            supabase.storage.from_(bucket_name).upload(
                path=file_path,
                file=content,
                file_options={"content-type": content_type, "upsert": "true"}
            )

            # The bucket is private, so we must create a signed URL.
            # Set expiration to 10 years to make it effectively permanent for our use case.
            TEN_YEARS_IN_SECONDS = 10 * 365 * 24 * 60 * 60  # 315,360,000
            signed_url_response = supabase.storage.from_(bucket_name).create_signed_url(
                path=file_path, expires_in=TEN_YEARS_IN_SECONDS
            )

            # The response is a dictionary, e.g., {'signedURL': '...'}
            public_url = signed_url_response.get("signedURL")

            if not public_url:
                raise StorageUploadError(f"Failed to create signed URL for {file_path}. Response: {signed_url_response}")

            logger.info(f"Successfully uploaded file '{file.filename}' and created signed URL.")
            return cast(str, public_url)

        except Exception as e:
            detailed_error_message = f"Storage upload failed: {e}"
            status_code = 500
            
            # Physical error recognition
            msg = str(e).lower()
            if "bucket not found" in msg:
                status_code = 404
            elif "permission denied" in msg or "not authorized" in msg:
                status_code = 403
            elif "too large" in msg:
                status_code = 413

            if hasattr(e, 'response') and e.response:
                try:
                    response_json = e.response.json()
                    detailed_error_message += f" Supabase response: {response_json}"
                except ValueError:
                    detailed_error_message += f" Supabase response text: {e.response.text}"
            
            logger.error(f"Failed to upload file to Supabase. Bucket: {bucket_name}, Error: {detailed_error_message}")
            raise StorageUploadError(detailed_error_message, status_code=status_code) from e

storage_service = StorageService()
