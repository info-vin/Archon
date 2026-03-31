"""
Projects Core API - Handles Project and Document life cycle.
"""

from datetime import UTC, datetime
from typing import Any, cast

from fastapi import APIRouter, Depends, Header, HTTPException, Response

from src.server.schemas.projects import (
    AssignableUser,
    CreateDocumentRequest,
    CreateProjectRequest,
    UpdateProjectRequest,
)

from ...auth.dependencies import get_current_user, requires_permission
from ...auth.permissions import TASK_CREATE, TASK_UPDATE_ALL
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
async def list_assignable_users(current_user: dict = Depends(get_current_user)):
    """Lists users that can be assigned tasks, respecting RBAC visibility."""
    current_user_role = current_user.get("role", "User")
    s, users = ProfileService().list_all_users()
    if not s or users is None:
        _err("Failed to retrieve profiles")

    rbac = RBACService()
    user_list = users if isinstance(users, list) else []
    user_dept = current_user.get("department")

    return [
        AssignableUser(id=str(u["id"]), name=str(u.get("full_name", u.get("name"))), role=str(u["role"]))
        for u in user_list
        if u.get("role") != "ai_agent"
        and rbac.has_permission_to_assign(current_user_role, str(u.get("role", "User")))
        and (current_user_role in ["system_admin", "admin"] or u.get("department") == user_dept)
    ]


@router.get("/projects")
async def list_projects(
    response: Response,
    include_content: bool = True,
    include_computed_status: bool = False,
    if_none_match: str | None = Header(None),
    current_user: dict = Depends(get_current_user),
):
    """Lists projects, with department isolation for non-admins."""
    u_role = current_user.get("role", "viewer").lower()
    u_dept = current_user.get("department")

    s, res = await ProjectService().list_projects(
        include_content=include_content, include_computed_status=include_computed_status
    )
    if not s or not isinstance(res, dict):
        _err(res)

    projs = res.get("projects", [])

    if u_role not in ["system_admin", "admin"]:
        projs = [p for p in projs if p.get("department") == u_dept or not p.get("department")]

    if include_content:
        projs = await SourceLinkingService().format_projects_with_sources(projs)

    etag = generate_etag({"projects": projs, "count": len(projs)})
    response.headers["ETag"] = etag
    if check_etag(if_none_match, etag):
        response.status_code = 304
        return None
    return {"projects": projs, "timestamp": datetime.now(UTC).isoformat(), "count": len(projs)}


@router.post("/projects")
async def create_project(req: CreateProjectRequest, current_user: dict = Depends(requires_permission(TASK_CREATE))):
    """Creates a new project. Requires TASK_CREATE permission."""
    if not req.title or not req.title.strip():
        _err("Title is required", 422)

    project_data = req.model_dump()
    project_data["department"] = current_user.get("department")

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
async def get_project(project_id: str, current_user: dict = Depends(get_current_user)):
    s, res = await ProjectService().get_project(project_id)
    if not s or not isinstance(res, dict) or not res.get("project"):
        _err(res if s else "Project not found", 404 if "not found" in str(res).lower() or s else 500)
    p = res.get("project", {})

    u_role = current_user.get("role", "viewer").lower()
    if (
        u_role not in ["system_admin", "admin"]
        and p.get("department")
        and p.get("department") != current_user.get("department")
    ):
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
async def update_project(project_id: str, req: UpdateProjectRequest, current_user: dict = Depends(get_current_user)):
    s, res = await ProjectService().get_project(project_id)
    if not s or not res.get("project"):
        _err("Project not found", 404)

    p = res["project"]
    u_role = current_user.get("role", "viewer").lower()
    if u_role not in ["system_admin", "admin"] and p.get("department") != current_user.get("department"):
        _err("Permission denied: Cannot update other department's projects.", 403)

    fields = {k: v for k, v in req.model_dump().items() if v is not None}
    s, res = await ProjectService().update_project(project_id, fields)
    if not s or not isinstance(res, dict):
        _err(res, 500)

    if req.technical_sources is not None or req.business_sources is not None:
        await SourceLinkingService().update_project_sources(
            project_id=project_id, technical_sources=req.technical_sources, business_sources=req.business_sources
        )
    return await SourceLinkingService().format_project_with_sources(res.get("project", {}))


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str, current_user: dict = Depends(requires_permission(TASK_UPDATE_ALL))):
    """Requires Admin level override for project deletion."""
    s, res = await ProjectService().delete_project(project_id)
    res_data = cast(dict[str, Any], handle_service_result(s, res))
    return {"message": "Project deleted successfully", "deleted_tasks": res_data.get("deleted_tasks", 0)}


@router.get("/projects/{project_id}/features")
async def get_project_features(project_id: str, current_user: dict = Depends(get_current_user)):
    s, res = await ProjectService().get_project_features(project_id)
    return handle_service_result(s, res)


@router.get("/projects/{project_id}/docs")
async def list_project_documents(
    project_id: str, include_content: bool = False, current_user: dict = Depends(get_current_user)
):
    s, res = DocumentService().list_documents(project_id, include_content)
    return handle_service_result(s, res)


@router.post("/projects/{project_id}/docs")
async def create_project_document(
    project_id: str, req: CreateDocumentRequest, current_user: dict = Depends(get_current_user)
):
    s, res = DocumentService().add_document(project_id=project_id, **req.model_dump())
    return {
        "message": "Document created successfully",
        "document": cast(dict[str, Any], handle_service_result(s, res)).get("document"),
    }


@router.get("/projects/{project_id}/docs/{doc_id}")
async def get_project_document(project_id: str, doc_id: str, current_user: dict = Depends(get_current_user)):
    s, res = DocumentService().get_document(project_id, doc_id)
    if not s or not isinstance(res, dict):
        _err(res, 404 if "not found" in str(res).lower() else 500)
    return res.get("document")
