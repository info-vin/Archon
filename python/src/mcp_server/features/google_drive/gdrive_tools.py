
"""
Google Drive integration tools for Archon MCP Server.
"""

import json
import logging
import os
from typing import Any

from mcp.server.fastmcp import Context, FastMCP

logger = logging.getLogger(__name__)


def register_gdrive_tools(mcp: FastMCP) -> None:
    """Register Google Drive integration tools with the MCP server."""

    @mcp.tool()
    async def gdrive_upload_file(
        ctx: Context, filename: str, content: str = "", mime_type: str = "text/plain", local_file_path: str = ""
    ) -> str:
        """
        Upload a file to Google Drive.

        Args:
            filename: The name of the file to create in Google Drive.
            content: The text content of the file (if uploading text).
            mime_type: The MIME type of the file. Defaults to 'text/plain'.
            local_file_path: Optional path to a local file to upload (overrides content).
        """
        token = os.getenv("GOOGLE_DRIVE_OAUTH_TOKEN")
        refresh_token = os.getenv("GOOGLE_DRIVE_REFRESH_TOKEN")
        client_id = os.getenv("GOOGLE_DRIVE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_DRIVE_CLIENT_SECRET")

        if not refresh_token or not client_id or not client_secret:
            logger.error("Missing Google Drive OAuth refresh credentials in environment.")
            return json.dumps(
                {"success": False, "error": "Missing Google Drive refresh credentials"}
            )

        try:
            import asyncio

            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload, MediaInMemoryUpload

            creds = Credentials(
                token=token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret
            )

            def _sync_upload() -> Any:
                service = build("drive", "v3", credentials=creds)
                file_metadata = {"name": filename}

                if mime_type == "text/plain" and not local_file_path:
                    file_metadata["mimeType"] = "application/vnd.google-apps.document"
                else:
                    file_metadata["mimeType"] = mime_type

                if local_file_path and os.path.exists(local_file_path):
                    media = MediaFileUpload(local_file_path, mimetype=mime_type, resumable=True)
                else:
                    media = MediaInMemoryUpload(
                        content.encode("utf-8"), mimetype=mime_type, resumable=True
                    )

                # Execute physical API request
                file = service.files().create(
                    body=file_metadata, media_body=media, fields="id"
                ).execute()

                return file.get("id")

            # Run in executor to prevent blocking the async event loop
            file_id = await asyncio.get_running_loop().run_in_executor(None, _sync_upload)

            return json.dumps(
                {
                    "success": True,
                    "file_id": file_id,
                    "message": f"Successfully uploaded '{filename}' to Google Drive.",
                    "filename": filename,
                }
            )
        except Exception as e:
            logger.error(f"Error in gdrive_upload_file: {e}")
            return json.dumps({"success": False, "error": str(e)})
