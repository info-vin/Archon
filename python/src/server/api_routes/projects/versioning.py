"""
Projects Versioning API - Handles version history and restoration.
"""

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException

from src.server.models.auth_models import UserProfileDTO
from src.server.schemas.projects import (
    CreateVersionRequest,
    CreateVersionResponse,
    RestoreVersionRequest,
    RestoreVersionResponse,
    VersionListResponse,
)
from src.server.services.projects.versioning_service import VersioningService
from src.server.services.shared_constants import RoleEnum
from src.server.utils.api_utils import handle_service_result

from ...auth.dependencies import get_current_user

router = APIRouter()


def _err(res: Any, code: int = 500):
    detail = res.get("error", res) if isinstance(res, dict) else res
    raise HTTPException(status_code=code, detail=detail)


@router.get("/versions", response_model=list[dict[str, Any]])
async def list_all_versions(current_user: UserProfileDTO = Depends(get_current_user)) -> list[dict[str, Any]]:
    u_role = current_user.role.lower()
    if u_role not in [RoleEnum.SYSTEM_ADMIN, RoleEnum.ADMIN, RoleEnum.MANAGER]:
        _err("Forbidden", 403)
    s, res = VersioningService().list_all_versions()
    if not s or not isinstance(res, dict):
        _err(res)
    return cast(list[dict[str, Any]], res.get("versions", []))


@router.get("/projects/{project_id}/versions", response_model=VersionListResponse)
async def list_project_versions(
    project_id: str, field_name: str | None = None, current_user: UserProfileDTO = Depends(get_current_user)
) -> VersionListResponse:
    s, res = VersioningService().list_versions(project_id, field_name)
    if not s or not isinstance(res, dict):
        _err(res, 404 if "not found" in str(res).lower() else 500)
    return VersionListResponse(
        versions=res.get("versions", []),
        total_count=res.get("total_count", 0),
    )


@router.post("/projects/{project_id}/versions", response_model=CreateVersionResponse)
async def create_project_version(
    project_id: str, req: CreateVersionRequest, current_user: UserProfileDTO = Depends(get_current_user)
) -> CreateVersionResponse:
    s, res = VersioningService().create_version(project_id=project_id, **req.model_dump())
    version_data = cast(dict[str, Any], handle_service_result(s, res)).get("version")
    return CreateVersionResponse(
        message="Version created successfully",
        version=version_data,
    )


@router.post(
    "/projects/{project_id}/versions/{field_name}/{version_number}/restore",
    response_model=RestoreVersionResponse,
)
async def restore_project_version(
    project_id: str,
    field_name: str,
    version_number: int,
    req: RestoreVersionRequest,
    current_user: UserProfileDTO = Depends(get_current_user),
) -> RestoreVersionResponse:
    s, res = VersioningService().restore_version(
        project_id=project_id, field_name=field_name, version_number=version_number, **req.model_dump()
    )
    result = cast(dict[str, Any], handle_service_result(s, res))
    return RestoreVersionResponse(
        message=f"Successfully restored {field_name} to version {version_number}",
        restored_content=result.get("restored_content"),
    )
