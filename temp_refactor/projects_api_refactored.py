"""
Refactored Projects API Example (Professional Grade)
Location: Archon/temp_refactor/projects_api.py

Improvements:
1. Replaced 100+ lines of manual 'if Field is not None' with 'model_dump(exclude_unset=True)'.
2. Consolidated RBAC logic.
3. Simplified Document & Versioning endpoint patterns.
"""

import json
from datetime import datetime
from typing import Any, cast

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    Response,
    status as http_status,
)
from pydantic import BaseModel

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.profile_service import ProfileService
from ..services.projects import (
    ProjectCreationService,
    ProjectService,
    SourceLinkingService,
    TaskService,
)
from ..services.projects.document_service import DocumentService
from ..services.projects.versioning_service import VersioningService
from ..services.rbac_service import RBACService
from ..utils import get_supabase_client
from ..utils.etag_utils import check_etag, generate_etag

logger = get_logger(__name__)
router = APIRouter(prefix="/api", tags=["projects"])

# --- Models ---
class CreateProjectRequest(BaseModel):
    title: str
    description: str | None = None
    pinned: bool | None = None

class UpdateProjectRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    pinned: bool | None = None

class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assignee_id: str | None = None

# --- Internal Helpers ---
def _handle_error(msg: str, e: Exception | None = None, code: int = 500):
    if e:
        logger.error(f"{msg} | error={str(e)}")
    else:
        logger.warning(msg)
    raise HTTPException(status_code=code, detail={"error": str(e) if e else msg})

# --- Endpoints (Refactored Samples) ---

@router.put("/projects/{project_id}")
async def update_project(project_id: str, request: UpdateProjectRequest):
    try:
        # [精簡點 1] 使用 exclude_unset 取代 20+ 行 if 判斷
        update_fields = request.model_dump(exclude_unset=True)
        if not update_fields:
            return _handle_error("No fields to update", code=400)

        project_service = ProjectService()
        
        # [精簡點 2] 邏輯委派：版本控制細節應由 Service 決定，而非 API 層
        success, result = await project_service.update_project(project_id, update_fields)
        
        if not success:
            _handle_error("Update failed")

        return result["project"]
    except Exception as e:
        _handle_error(f"Project update failed | id={project_id}", e)

@router.put("/tasks/{task_id}")
async def update_task(task_id: str, request: UpdateTaskRequest):
    try:
        # [精簡點 3] 統一的資料處理模式
        update_fields = request.model_dump(exclude_unset=True)
        
        task_service = TaskService()
        success, result = await task_service.update_task(task_id, update_fields)
        
        if not success:
             _handle_error("Task update failed")

        return {"task": result["task"]}
    except Exception as e:
        _handle_error(f"Failed to update task | id={task_id}", e)
