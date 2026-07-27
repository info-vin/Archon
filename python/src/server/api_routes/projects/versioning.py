"""
Projects Versioning API - Handles version history and restoration.
"""

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException

from src.server.models.auth_models import UserProfileDTO
from src.server.schemas.projects import (
    CreateVersionRequest,
    RestoreVersionRequest,
)
from src.server.services.projects.versioning_service import VersioningService
from src.server.utils.api_utils import handle_service_result

from ...auth.dependencies import get_current_user

router = APIRouter()


def _err(res: Any, code: int = 500):
    detail = res.get("error", res) if isinstance(res, dict) else res
    raise HTTPException(status_code=code, detail=detail)


@router.get("/versions")
async def list_all_versions(current_user: UserProfileDTO = Depends(get_current_user)):
    u_role = current_user.role.lower()
    if u_role not in ["system_admin", "admin", "manager"]:
        _err("Forbidden", 403)
    s, res = VersioningService().list_all_versions()
    if not s or not isinstance(res, dict):
        _err(res)
    return res.get("versions", [])


@router.get("/projects/{project_id}/versions")
async def list_project_versions(
    project_id: str, field_name: str | None = None, current_user: UserProfileDTO = Depends(get_current_user)
):
    s, res = VersioningService().list_versions(project_id, field_name)
    if not s:
        _err(res, 404 if "not found" in str(res).lower() else 500)
    return res


@router.post("/projects/{project_id}/versions")
async def create_project_version(
    project_id: str, req: CreateVersionRequest, current_user: UserProfileDTO = Depends(get_current_user)
):
    s, res = VersioningService().create_version(project_id=project_id, **req.model_dump())
    return {
        "message": "Version created successfully",
        "version": cast(dict[str, Any], handle_service_result(s, res)).get("version"),
    }


@router.post("/projects/{project_id}/versions/{field_name}/{version_number}/restore")
async def restore_project_version(
    project_id: str,
    field_name: str,
    version_number: int,
    req: RestoreVersionRequest,
    current_user: UserProfileDTO = Depends(get_current_user),
):
    s, res = VersioningService().restore_version(
        project_id=project_id, field_name=field_name, version_number=version_number, **req.model_dump()
    )
    return {
        "message": f"Successfully restored {field_name} to version {version_number}",
        **cast(dict[str, Any], handle_service_result(s, res)),
    }
