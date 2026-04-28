# python/src/server/utils/google_storage.py

import asyncio
import logging
from typing import Any

from google import genai

logger = logging.getLogger(__name__)

class GoogleStorageHandler:
    """
    Physical Handler for Google Files API (Phase 4.6.46 Hardened).
    Specialized in large file uploads (20MB+) with async polling.
    """

    @staticmethod
    async def upload_and_wait(client: genai.Client, path: str, display_name: str = "Audio File") -> Any:
        """
        Uploads a file and polls until its state is 'ACTIVE'.
        Ensures resilience for Alice's long field recordings.
        """
        try:
            # 1. Physical Upload
            uploaded_file = client.files.upload(path=path)
            logger.info(f"GoogleStorage: File {uploaded_file.name} ({display_name}) uploaded. Polling...")

            # 2. Resilience Polling (Restored from 4/16 golden standard)
            max_retries = 45  # Increased to 90s for extra large files
            poll_interval = 2

            for i in range(max_retries):
                file_info = client.files.get(name=uploaded_file.name)
                state = file_info.state.name

                if state == "ACTIVE":
                    logger.info(f"GoogleStorage: File {uploaded_file.name} is ACTIVE after {i*poll_interval}s.")
                    return file_info
                elif state == "FAILED":
                    raise Exception(f"Google Files API reported FAILURE for {uploaded_file.name}")

                await asyncio.sleep(poll_interval)

            raise TimeoutError(f"GoogleStorage: Timeout waiting for {display_name} to become ACTIVE.")

        except Exception as e:
            logger.error(f"GoogleStorage: Upload/Poll failed: {e}")
            raise e
