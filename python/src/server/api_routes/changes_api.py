"""
Changes API Hardened - Secure Inbox for AI proposed changes.
Ensures only authorized Managers and Admins can approve or reject proposals.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.server.auth.dependencies import get_current_user, requires_permission
from src.server.auth.permissions import CODE_APPROVE, TASK_READ_TEAM
from src.server.services.propose_change_service import ProposeChangeService

router = APIRouter(prefix="/api/changes", tags=["Changes"])

@router.get("", response_model=list[dict[str, Any]])
async def list_proposals(current_user: dict = Depends(get_current_user)):
    """Lists all pending AI proposals. Respects department isolation."""
    service = ProposeChangeService()
    # Logic inside service should filter by department for non-admins
    return await service.list_proposals(user_id=str(current_user.get("id")))

@router.get("/{change_id}")
async def get_proposal(change_id: UUID, current_user: dict = Depends(get_current_user)):
    """Retrieves a specific proposal with Diff data."""
    service = ProposeChangeService()
    res = await service.get_proposal(change_id)
    if not res:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return res

@router.post("/{change_id}/approve")
async def approve_proposal(
    change_id: UUID,
    current_user: dict = Depends(requires_permission(CODE_APPROVE))
):
    """Executes the proposed change. Requires CODE_APPROVE permission."""
    service = ProposeChangeService()
    try:
        res = await service.approve_proposal(change_id, user_id=current_user.get("id"))
        return {"status": "success", "message": "Change approved and executed", "details": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@router.post("/{change_id}/reject")
async def reject_proposal(
    change_id: UUID,
    current_user: dict = Depends(requires_permission(TASK_READ_TEAM))
):
    """Rejects the proposal. Requires Manager level visibility."""
    service = ProposeChangeService()
    try:
        res = await service.reject_proposal(change_id, user_id=current_user.get("id"))
        return {"status": "rejected", "message": "Change proposal rejected", "details": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
