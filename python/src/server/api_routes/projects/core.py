"""
Projects Core API - Handles Project and Document life cycle.
"""

from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from src.server.models.auth_models import UserProfileDTO
from src.server.schemas.projects import (
    AssignableUser,
    CreateDocumentRequest,
    CreateProjectRequest,
    UpdateProjectRequest,
)
from src.server.services.projects.project_service import (
    ProjectDTO,
    ProjectListResultDTO,
    ProjectResultDTO,
    ProjectUpdateDTO,
)

from ...auth.dependencies import get_current_user, requires_permission
from ...auth.permissions import TASK_CREATE, TASK_READ_TEAM, TASK_UPDATE_ALL
from ...services.profile_service import ProfileService
from ...services.projects.document_service import DocumentService
from ...services.projects.project_creation_service import ProjectCreationService
from ...services.projects.project_service import ProjectService
from ...services.projects.source_linking_service import SourceLinkingService
from ...services.rbac_service import RBACService
from ...utils.api_utils import handle_service_result
from ...utils.etag_utils import check_etag, generate_etag

router = APIRouter()


def _err(res: Any, code: int = 500):
    detail = res.get("error", res) if isinstance(res, dict) else res
    raise HTTPException(status_code=code, detail=detail)


@router.get("/assignable-users", response_model=list[AssignableUser])
async def list_assignable_users(current_user: UserProfileDTO = Depends(get_current_user)):
    """Lists users that can be assigned tasks, respecting RBAC visibility."""
    current_user_role = current_user.role
    s, users = ProfileService().list_all_users()
    if not s or users is None:
        _err("Failed to retrieve profiles")

    rbac = RBACService()
    user_list = users if isinstance(users, list) else []

    filtered_users = []
    for u in user_list:
        if u.role == "ai_agent":
            continue
        can_assign = await rbac.has_permission_to_assign(current_user_role, str(u.role))
        if can_assign and rbac.validate_project_access(u, current_user):
            filtered_users.append(
                AssignableUser(id=str(u.id), name=str(u.name), role=str(u.role))
            )

    return filtered_users


@router.get("/projects")
async def list_projects(
    response: Response,
    include_content: bool = True,
    include_computed_status: bool = False,
    if_none_match: str | None = Header(None),
    current_user: UserProfileDTO = Depends(requires_permission(TASK_READ_TEAM)),
):
    """Lists projects, with department isolation managed by RBACService."""
    s, res = await ProjectService().list_projects(
        include_content=include_content, include_computed_status=include_computed_status
    )
    if not s or not isinstance(res, dict):
        _err(res)

    res_dto = cast(ProjectListResultDTO, res)
    projs = res_dto.get("projects", [])
    projs = cast(list[ProjectDTO], RBACService().scope_projects(cast(list[dict[str, Any]], projs), current_user))

    if include_content:
        projs = cast(list[ProjectDTO], await SourceLinkingService().format_projects_with_sources(cast(list[dict[str, Any]], projs)))

    etag = generate_etag({"projects": projs, "count": len(projs)})
    response.headers["ETag"] = etag
    if check_etag(if_none_match, etag):
        response.status_code = 304
        return None
    return {"projects": projs, "timestamp": datetime.now(UTC).isoformat(), "count": len(projs)}


@router.post("/projects")
async def create_project(req: CreateProjectRequest, current_user: UserProfileDTO = Depends(requires_permission(TASK_CREATE))):
    """Creates a new project. Requires TASK_CREATE permission."""
    if not req.title or not req.title.strip():
        _err("Title is required", 422)

    project_data = req.model_dump()
    project_data["department"] = current_user.department

    s, res = await ProjectCreationService().create_project_with_ai(progress_id="direct", **project_data)
    if s and isinstance(res, dict):
        return {
            "project_id": res.get("project_id"),
            "project": res.get("project"),
            "status": "completed",
            "message": f"Project '{req.title}' created successfully",
        }
    _err(res)


@router.get("/projects/{project_id}")
async def get_project(project_id: str, current_user: UserProfileDTO = Depends(get_current_user)):
    s, res = await ProjectService().get_project(project_id)
    if not s or not isinstance(res, dict) or not res.get("project"):
        _err(res if s else "Project not found", 404 if "not found" in str(res).lower() or s else 500)
    res_dto2 = cast(ProjectResultDTO, res)
    p = res_dto2.get("project", {})

    if not RBACService().validate_project_access(cast(dict[str, Any], p), current_user):
        _err("Access denied to this department's project.", 403)

    return {
        **p,
        "description": p.get("description", ""),
        "docs": p.get("docs", []),
        "features": p.get("features", []),
        "data": p.get("data", []),
        "pinned": p.get("pinned", False),
    }


@router.patch("/projects/{project_id}")
async def update_project(project_id: str, req: UpdateProjectRequest, current_user: UserProfileDTO = Depends(get_current_user)):
    s, res = await ProjectService().get_project(project_id)
    res_dto3 = cast(ProjectResultDTO, res)
    if not s or not res_dto3.get("project"):
        _err("Project not found", 404)

    p = res_dto3["project"]
    if not RBACService().validate_project_access(cast(dict[str, Any], p), current_user):
        _err("Permission denied: Cannot update other department's projects.", 403)

    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    s, res = await ProjectService().update_project(project_id, cast(ProjectUpdateDTO, fields))
    if not s or not isinstance(res, dict):
        _err(res, 500)

    if req.technical_sources is not None or req.business_sources is not None:
        await SourceLinkingService().update_project_sources(
            project_id=project_id, technical_sources=req.technical_sources, business_sources=req.business_sources
        )
    return await SourceLinkingService().format_project_with_sources(cast(dict[str, Any], cast(ProjectResultDTO, res).get("project", {})))


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: UserProfileDTO = Depends(requires_permission(TASK_UPDATE_ALL))):
    """Requires Admin level override for project deletion."""
    s, res = await ProjectService().delete_project(project_id)
    res_data = cast(dict[str, Any], handle_service_result(s, cast(Any, res)))
    return {"message": "Project deleted successfully", "deleted_tasks": res_data.get("deleted_tasks", 0)}


@router.get("/projects/{project_id}/features")
async def get_project_features(project_id: str, current_user: UserProfileDTO = Depends(get_current_user)):
    s, res = await ProjectService().get_project_features(project_id)
    return handle_service_result(s, cast(Any, res))


@router.get("/projects/{project_id}/docs")
async def list_project_documents(
    project_id: str, include_content: bool = False, current_user: UserProfileDTO = Depends(get_current_user)
):
    s, res = DocumentService().list_documents(project_id, include_content)
    return handle_service_result(s, cast(Any, res))


@router.post("/projects/{project_id}/docs")
async def create_project_document(
    project_id: str, req: CreateDocumentRequest, current_user: UserProfileDTO = Depends(get_current_user)
):
    s, res = DocumentService().add_document(project_id=project_id, **req.model_dump())
    return {
        "message": "Document created successfully",
        "document": cast(dict[str, Any], handle_service_result(s, cast(Any, res))).get("document"),
    }


@router.get("/projects/{project_id}/docs/{doc_id}")
async def get_project_document(project_id: str, doc_id: str, current_user: UserProfileDTO = Depends(get_current_user)):
    s, res = DocumentService().get_document(project_id, doc_id)
    if not s or not isinstance(res, dict):
        _err(res, 404 if "not found" in str(res).lower() else 500)
    return res.get("document")
