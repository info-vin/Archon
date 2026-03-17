from fastapi import APIRouter

# EXPORTS for testing and facade compatibility (Explicit re-export for Ruff)
from src.server.services.projects.document_service import DocumentService as DocumentService
from src.server.services.projects.project_creation_service import ProjectCreationService as ProjectCreationService
from src.server.services.projects.project_service import ProjectService as ProjectService
from src.server.services.projects.source_linking_service import SourceLinkingService as SourceLinkingService
from src.server.services.projects.task_service import TaskService as TaskService
from src.server.services.projects.versioning_service import VersioningService as VersioningService

from .core import router as core_router
from .ops import router as ops_router
from .versioning import router as versioning_router

router = APIRouter()

# CRITICAL: Include ops_router BEFORE core_router to ensure static routes
# like /projects/task-counts take precedence over dynamic /projects/{project_id}
router.include_router(ops_router)
router.include_router(core_router)
router.include_router(versioning_router)
