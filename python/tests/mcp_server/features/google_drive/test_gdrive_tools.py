"""Unit tests for Google Drive MCP tools."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from mcp.server.fastmcp import Context

from src.mcp_server.features.google_drive.gdrive_tools import register_gdrive_tools


@pytest.fixture
def mock_mcp():
    """Create a mock MCP server for testing."""
    mock = MagicMock()
    mock._tools = {}

    def tool_decorator(*args, **kwargs):
        def decorator(func):
            mock._tools[func.__name__] = func
            return func

        return decorator

    mock.tool = tool_decorator
    return mock


@pytest.mark.asyncio
async def test_gdrive_upload_file_missing_token(mock_mcp):
    """Test gdrive_upload_file fails fast when token is missing."""
    register_gdrive_tools(mock_mcp)

    upload_file = mock_mcp._tools.get("gdrive_upload_file")
    assert upload_file is not None

    ctx = MagicMock(spec=Context)

    # Ensure token is missing
    with patch.dict(os.environ, clear=True):
        res_str = await upload_file(ctx, filename="test.txt", content="hello")
        res = json.loads(res_str)

        assert res["success"] is False
        assert "Missing Google Drive refresh credentials" in res["error"]


@pytest.mark.asyncio
async def test_gdrive_upload_file_success(mock_mcp):
    """Test gdrive_upload_file works when token is present and API mock succeeds."""
    register_gdrive_tools(mock_mcp)

    upload_file = mock_mcp._tools.get("gdrive_upload_file")

    ctx = MagicMock(spec=Context)

    # Mock the google API client build and Credentials
    env_mock = {
        "GOOGLE_DRIVE_OAUTH_TOKEN": "fake-token",
        "GOOGLE_DRIVE_REFRESH_TOKEN": "fake-refresh",
        "GOOGLE_DRIVE_CLIENT_ID": "fake-client",
        "GOOGLE_DRIVE_CLIENT_SECRET": "fake-secret"
    }
    with patch.dict(os.environ, env_mock):
        with patch("google.oauth2.credentials.Credentials"):
            with patch("googleapiclient.discovery.build") as mock_build:

                # Setup the mock service
                mock_service = MagicMock()
                mock_build.return_value = mock_service

                mock_files = MagicMock()
                mock_service.files.return_value = mock_files

                mock_create = MagicMock()
                mock_files.create.return_value = mock_create

                mock_create.execute.return_value = {"id": "real_file_12345"}

                res_str = await upload_file(ctx, filename="test.txt", content="hello")
                res = json.loads(res_str)

                assert res["success"] is True
                assert res["file_id"] == "real_file_12345"
                assert res["filename"] == "test.txt"

                # Verify mock was called with correct structure
                mock_files.create.assert_called_once()
                call_kwargs = mock_files.create.call_args[1]
                assert call_kwargs["body"]["name"] == "test.txt"
                assert call_kwargs["body"]["mimeType"] == "application/vnd.google-apps.document"
