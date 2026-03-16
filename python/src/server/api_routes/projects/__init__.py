from fastapi import APIRouter
from .ops import router as ops_router
from .core import router as core_router
from .versioning import router as versioning_router

# EXPORTS for testing and facade compatibility
from src.server.services.projects.project_service import ProjectService
from src.server.services.projects.task_service import TaskService
from src.server.services.projects.project_creation_service import ProjectCreationService
from src.server.services.projects.document_service import DocumentService
from src.server.services.projects.versioning_service import VersioningService
from src.server.services.projects.source_linking_service import SourceLinkingService

router = APIRouter()

# CRITICAL: Include ops_router BEFORE core_router to ensure static routes 
# like /projects/task-counts take precedence over dynamic /projects/{project_id}
router.include_router(ops_router)
router.include_router(core_router)
router.include_router(versioning_router)
