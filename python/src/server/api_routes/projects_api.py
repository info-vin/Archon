"""
Projects API Facade (Phase 4.6.12 Hardening)
Entry point for project-related routes, delegating to modular sub-routers.
Maintains 100% Signature Alignment for Test Compatibility.
"""

from fastapi import APIRouter

from ..services.profile_service import ProfileService
from ..services.projects.document_service import DocumentService
from ..services.projects.project_creation_service import ProjectCreationService

# EXPORTS for service & test compatibility (Maintaining facade pattern)
from ..services.projects.project_service import ProjectService
from ..services.projects.source_linking_service import SourceLinkingService
from ..services.projects.task_service import TaskService
from ..services.projects.versioning_service import VersioningService
from ..services.rbac_service import RBACService

# Import sub-routers from the modular package
from .projects import router as projects_aggregator_router

# Use /api as prefix to flatten paths for FE, aligned with knowledge_api pattern
router = APIRouter(prefix="/api", tags=["projects"])

# Include the aggregated modular router
router.include_router(projects_aggregator_router)

__all__ = [
    "router",
    "ProjectService",
    "TaskService",
    "ProjectCreationService",
    "DocumentService",
    "VersioningService",
    "ProfileService",
    "RBACService",
    "SourceLinkingService"
]
