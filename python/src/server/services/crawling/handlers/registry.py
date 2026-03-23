from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..crawling_service import CrawlingService

# Global registry to track active orchestration services for cancellation support
# Physically isolated to prevent circular dependencies during refactoring.
_active_orchestrations: dict[str, "CrawlingService"] = {}


def get_active_orchestration(progress_id: str) -> Optional["CrawlingService"]:
    """Get an active orchestration service by progress ID."""
    return _active_orchestrations.get(progress_id)


def register_orchestration(progress_id: str, orchestration: "CrawlingService"):
    """Register an active orchestration service."""
    _active_orchestrations[progress_id] = orchestration


def unregister_orchestration(progress_id: str):
    """Unregister an orchestration service."""
    if progress_id in _active_orchestrations:
        del _active_orchestrations[progress_id]
