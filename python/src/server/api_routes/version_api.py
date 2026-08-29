"""
API routes for version checking and update management.
"""

from datetime import datetime
from typing import Any

import logfire
from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel, Field

from ..auth.dependencies import requires_permission
from ..auth.permissions import TASK_READ_TEAM
from ..config.version import ARCHON_VERSION
from ..services.version_service import version_service
from ..utils.etag_utils import check_etag, generate_etag


# Response models
class ReleaseAsset(BaseModel):
    """Represents a downloadable asset from a release."""

    name: str = Field(description="Name of the release asset")
    size: int = Field(description="Size of the asset in bytes")
    download_count: int = Field(description="Total download count for this asset")
    browser_download_url: str = Field(description="Direct browser download URL")
    content_type: str = Field(description="MIME type of the asset")


class VersionCheckResponse(BaseModel):
    """Version check response with update information."""

    current: str = Field(description="Currently installed version")
    latest: str | None = Field(default=None, description="Latest available version tag")
    update_available: bool = Field(description="Whether a newer version is available")
    release_url: str | None = Field(default=None, description="URL to the GitHub release notes")
    release_notes: str | None = Field(default=None, description="Markdown changelog or release body")
    published_at: datetime | None = Field(default=None, description="Publication timestamp of the release")
    check_error: str | None = Field(default=None, description="Error message if update check failed")
    assets: list[ReleaseAsset] | None = Field(default=None, description="List of release assets")
    author: str | None = Field(default=None, description="GitHub author username of the release")


class CurrentVersionResponse(BaseModel):
    """Simple current version response."""

    version: str = Field(description="Installed version string")
    timestamp: datetime = Field(description="Server timestamp when check occurred")


class ClearCacheResponse(BaseModel):
    """Response returned when version cache is cleared."""

    message: str = Field(description="Status message")
    success: bool = Field(description="Indicates if cache clearing was successful")


class DocumentVersionResponse(BaseModel):
    """Document historical version data."""

    id: str | None = Field(default=None, description="Version ID")
    project_id: str | None = Field(default=None, description="Associated project ID")
    task_id: str | None = Field(default=None, description="Associated task ID")
    field_name: str | None = Field(default=None, description="Document field name")
    version_number: int | None = Field(default=None, description="Version sequence number")
    content: dict[str, Any] | None = Field(default=None, description="Document snapshot content")
    change_summary: str | None = Field(default=None, description="Summary of changes in version")
    change_type: str | None = Field(default=None, description="Type of document change")
    document_id: str | None = Field(default=None, description="Associated document ID")
    created_by: str | None = Field(default=None, description="User ID who created version")
    created_at: str | None = Field(default=None, description="Creation timestamp ISO string")
    status: str | None = Field(default=None, description="Status of the version entry")


# Create router
router = APIRouter(prefix="/api/version", tags=["version"])


@router.get("/documents", response_model=list[DocumentVersionResponse])
async def get_document_versions(
    limit: int = 50, current_user: dict = Depends(requires_permission(TASK_READ_TEAM))
) -> list[DocumentVersionResponse]:
    """
    Fetch historical versions of project documents. Requires TASK_READ_TEAM.
    """
    try:
        raw_versions = await version_service.get_document_versions(limit=limit)
        return [DocumentVersionResponse(**v) for v in raw_versions]
    except Exception as e:
        logfire.error(f"Error fetching document versions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/check", response_model=VersionCheckResponse)
async def check_for_updates(
    response: Response, if_none_match: str | None = Header(None)
) -> VersionCheckResponse | Response:
    """
    Check for available Archon updates.

    Queries GitHub releases API to determine if a newer version is available.
    Results are cached for 1 hour to avoid rate limiting.

    Returns:
        Version information including current, latest, and update availability
    """
    try:
        # Get version check results from service
        result = await version_service.check_for_updates()

        # Generate ETag for response
        etag = generate_etag(result)

        # Check if client has current data
        if check_etag(if_none_match, etag):
            # Client has current data, return 304
            response.status_code = 304
            response.headers["ETag"] = f'"{etag}"'
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
            return Response(status_code=304)
        else:
            # Client needs new data
            response.headers["ETag"] = f'"{etag}"'
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
            return VersionCheckResponse(**result)  # type: ignore[arg-type]

    except Exception as e:
        logfire.error(f"Error checking for updates: {e}")
        # Return safe response with error
        return VersionCheckResponse(
            current=ARCHON_VERSION,
            latest=None,
            update_available=False,
            release_url=None,
            release_notes=None,
            published_at=None,
            check_error=str(e),
        )


@router.get("/current", response_model=CurrentVersionResponse)
async def get_current_version() -> CurrentVersionResponse:
    """
    Get the current Archon version.

    Simple endpoint that returns the installed version without checking for updates.
    """
    return CurrentVersionResponse(version=ARCHON_VERSION, timestamp=datetime.now())


@router.post("/clear-cache", response_model=ClearCacheResponse)
async def clear_version_cache() -> ClearCacheResponse:
    """
    Clear the version check cache.

    Forces the next version check to query GitHub API instead of using cached data.
    Useful for testing or forcing an immediate update check.
    """
    try:
        version_service.clear_cache()
        return ClearCacheResponse(message="Version cache cleared successfully", success=True)
    except Exception as e:
        logfire.error(f"Error clearing version cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}") from e
