"""
Projects Ops API - Handles Tasks, AI Dispatching, and Agent Callbacks.
"""

from typing import Any, cast

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from src.server.auth.dependencies import get_current_user, requires_permission
from src.server.auth.permissions import AGENT_TRIGGER_DEV
from src.server.schemas.projects import (
    AgentOutputUpdateRequest,
    AgentStatusUpdateRequest,
    CreateTaskRequest,
    GenerateTaskFromAlertRequest,
    RefineTaskRequest,
    UpdateTaskRequest,
)

from ...services.profile_service import ProfileService
from ...services.projects.task_service import TaskService
from ...services.rbac_service import RBACService
from ...utils.api_utils import handle_service_result
from ...utils.etag_utils import check_etag, generate_etag

router = APIRouter()

def _err(res: Any, code: int = 500):
    detail = res.get("error", res) if isinstance(res, dict) else res
    raise HTTPException(status_code=code, detail=detail)

@router.get("/projects/task-counts")
async def get_all_task_counts(request: Request, response: Response, current_user: dict = Depends(get_current_user)):
    s, res = await TaskService().get_all_project_task_counts()
    if not s:
        _err(res)
    etag = generate_etag({"counts": res, "count": len(res if isinstance(res, dict) else [])})
    response.headers["ETag"] = etag
    if check_etag(request.headers.get("If-None-Match"), etag):
        response.status_code = 304
        return None
    return res

@router.get("/projects/{project_id}/tasks")
async def list_project_tasks(
    project_id: str,
    req: Request,
    response: Response,
    include_archived: bool = False,
    exclude_large_fields: bool = False,
    current_user: dict = Depends(get_current_user)
):
    s, res = await TaskService().list_tasks(project_id=project_id, include_closed=True, exclude_large_fields=exclude_large_fields, include_archived=include_archived)
    if not s or not isinstance(res, dict):
        _err(res)
    tasks = res.get("tasks", [])
    etag = generate_etag({"tasks": tasks, "project_id": project_id})
    response.headers["ETag"] = etag
    if check_etag(req.headers.get("If-None-Match"), etag):
        response.status_code = 304
        return None
    return tasks

@router.post("/tasks/refine-description")
async def refine_task_description(req: RefineTaskRequest, current_user: dict = Depends(get_current_user)):
    res = await TaskService().refine_task_description(req.title, req.description)
    return {"refined_description": res}

@router.post("/tasks/generate-from-alert")
async def generate_task_from_alert(
    req: GenerateTaskFromAlertRequest,
    current_user: dict = Depends(requires_permission(AGENT_TRIGGER_DEV))
):
    s, res = await TaskService().generate_task_from_alert(alert_id=req.alert_id, assignee_id=req.assignee_id)
    return handle_service_result(s, res)

@router.post("/tasks")
async def create_task(req: CreateTaskRequest, current_user: dict = Depends(get_current_user)):
    """Creates a new task. Includes cross-department assignment blocking."""
    u_role = current_user.get("role", "viewer").lower()
    u_dept = current_user.get("department")

    target_name, res_id = req.assignee, req.assignee_id
    if res_id:
        from src.server.services.shared_constants import AI_AGENT_ROLES
        if res_id in AI_AGENT_ROLES.values():
            res_id = None
            for n, aid in AI_AGENT_ROLES.items():
                if aid == req.assignee_id:
                    target_name = n.split(" ")[0]
                    break
        else:
            ok, p = ProfileService().get_profile(str(req.assignee_id))
            if ok and isinstance(p, dict):
                target_name = str(p.get("name"))
                if u_role not in ["system_admin", "admin"] and p.get("department") != u_dept:
                    _err(f"Cannot assign tasks to members outside your department ({p.get('department')})", 403)

    s, res = await TaskService().create_task(project_id=req.project_id, title=req.title, description=req.description or "", assignee=target_name or "User", assignee_id=res_id, priority=req.priority or "medium", task_order=req.task_order or 0, feature=req.feature, due_date=req.due_date, knowledge_source_ids=req.knowledge_source_ids, is_recurring=req.is_recurring or False, crawler_target_id=req.crawler_target_id, schedule_config=req.schedule_config)
    if not s or not isinstance(res, dict):
        _err(res, 400)
    return {"message": "Task created successfully", "task": res.get("task")}

@router.get("/tasks")
async def list_tasks(
    status: str | None = None,
    project_id: str | None = None,
    assignee_id: str | None = None,
    include_closed: bool = False,
    include_unassigned: bool = False,
    page: int = 1,
    per_page: int = 50,
    exclude_large_fields: bool = False,
    current_user: dict = Depends(get_current_user)
):
    u_role = current_user.get("role", "member").lower()
    u_id = current_user.get("id")

    if u_role in ["system_admin", "admin", "manager"]:
        a_filter = assignee_id
    else:
        a_filter = u_id

    s, res = await TaskService().list_tasks(
        project_id=project_id if project_id and project_id.lower() != 'all' else None,
        status=status or "",
        include_closed=include_closed,
        exclude_large_fields=exclude_large_fields,
        assignee_id=a_filter,
        include_unassigned=include_unassigned if u_role in ["admin", "manager"] else False
    )

    data = cast(dict[str, Any], handle_service_result(s, res))
    tasks = data.get("tasks", [])

    return {
        "tasks": tasks[(page-1)*per_page : page*per_page],
        "pagination": {
            "total": len(tasks),
            "page": page,
            "per_page": per_page,
            "pages": (len(tasks)+per_page-1)//per_page
        }
    }

@router.get("/tasks/{task_id}")
async def get_task(task_id: str, current_user: dict = Depends(get_current_user)):
    s, res = await TaskService().get_task(task_id)
    return cast(dict[str, Any], handle_service_result(s, res)).get("task")

@router.put("/tasks/{task_id}")
async def update_task(task_id: str, req: UpdateTaskRequest, current_user: dict = Depends(get_current_user)):
    u_role = current_user.get("role", "viewer").lower()
    fields = {k: v for k, v in req.model_dump().items() if v is not None}

    if "assignee" in fields or "assignee_id" in fields:
        name = fields.get("assignee")
        if name and name != "Unassigned":
            ok, r = ProfileService().get_user_role(str(name))
            if ok and r and not RBACService().has_permission_to_assign(u_role, r):
                _err("Forbidden: Cannot reassign to this role", 403)

    s, res = await TaskService().update_task(task_id, fields)
    return {"message": "Task updated successfully", "task": cast(dict[str, Any], handle_service_result(s, res)).get("task")}

@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: dict = Depends(get_current_user)):
    if current_user.get("role", "member").lower() not in ["system_admin", "admin", "manager"]:
        _err("Forbidden: Only managers can archive tasks", 403)
    s, res = await TaskService().archive_task(task_id, archived_by=str(current_user.get("id")))
    if not s:
        _err(res, 400)
    return {"message": "Task archived successfully"}

@router.post("/tasks/{task_id}/agent-status", tags=["Agent Callback"])
async def report_task_status_from_agent(task_id: str, req: AgentStatusUpdateRequest):
    s, res = await TaskService().update_task_status_from_agent(task_id=task_id, new_status=req.status, agent_id=req.agent_id)
    if not s:
        _err(res, 400)
    return res

@router.post("/tasks/{task_id}/agent-output", tags=["Agent Callback"])
async def report_task_output_from_agent(task_id: str, req: AgentOutputUpdateRequest):
    s, res = await TaskService().save_agent_output(task_id=task_id, output=req.output, agent_id=req.agent_id)
    if not s:
        _err(res, 400)
    return res
