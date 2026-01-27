from fastapi import APIRouter, Depends, HTTPException, status
from ..services.health_service import HealthService
from ..auth.dependencies import get_current_user
from typing import Dict, Any

router = APIRouter(tags=["System"])

async def require_system_admin(user=Depends(get_current_user)):
    """
    Dependency to ensure the user has SYSTEM_ADMIN role.
    """
    # Use string comparison as EmployeeRole enum is not yet standardized in backend
    if user.get("role") != "system_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Requires System Administrator privileges."
        )
    return user

@router.get("/health/rag", dependencies=[Depends(require_system_admin)])
async def get_rag_health_check() -> dict[str, Any]:
    """
    Performs a deep integrity check of the RAG system.
    WARNING: This performs DB writes (seeding) and should not be called frequently.
    """
    service = HealthService()
    return await service.check_rag_integrity()
