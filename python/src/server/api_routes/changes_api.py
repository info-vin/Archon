"""
Changes API Hardened - Secure Inbox for AI proposed changes.
Ensures only authorized Managers and Admins can approve or reject proposals.
"""

from typing import cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from src.server.models.auth_models import UserProfileDTO
from src.server.schemas.changes import (
    CreateProposalRequest,
    ProposalActionResultResponse,
    ProposalResponse,
)
from src.server.services.propose_change_service import ProposeChangeService

from ..auth.dependencies import get_current_user, requires_permission
from ..auth.permissions import CODE_APPROVE, TASK_READ_TEAM

router = APIRouter(prefix="/api/changes", tags=["Changes"])


@router.get("", response_model=list[ProposalResponse])
async def list_proposals(current_user: UserProfileDTO = Depends(get_current_user)) -> list[ProposalResponse]:
    """Lists all pending AI proposals. Respects department isolation."""
    service = ProposeChangeService()
    res = await service.list_proposals(user_id=str(current_user.id))
    return cast(list[ProposalResponse], res)


@router.post("", response_model=ProposalResponse)
async def create_proposal(
    payload: CreateProposalRequest, current_user: UserProfileDTO = Depends(get_current_user)
) -> ProposalResponse:
    """Creates a new AI proposal. Typically called by an Agent."""
    service = ProposeChangeService()
    if not payload.file_path or payload.new_content is None:
        raise HTTPException(status_code=400, detail="Missing file_path or new_content")

    res = await service.create_file_proposal(
        file_path=payload.file_path,
        new_content=payload.new_content,
        summary=payload.summary,
        user_id=str(current_user.id),
    )
    return cast(ProposalResponse, res)


@router.get("/{change_id}", response_model=ProposalResponse)
async def get_proposal(change_id: UUID, current_user: UserProfileDTO = Depends(get_current_user)) -> ProposalResponse:
    """Retrieves a specific proposal with Diff data."""
    service = ProposeChangeService()
    res = await service.get_proposal(change_id)
    if not res:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return cast(ProposalResponse, res)


@router.post("/{change_id}/approve", response_model=ProposalActionResultResponse)
async def approve_proposal(
    change_id: UUID, current_user: UserProfileDTO = Depends(requires_permission(CODE_APPROVE))
) -> ProposalActionResultResponse:
    """Executes the proposed change. Requires CODE_APPROVE permission."""
    service = ProposeChangeService()
    try:
        res = await service.approve_proposal(change_id, user_id=current_user.id)
        return cast(
            ProposalActionResultResponse,
            {"status": "success", "message": "Change approved and executed", "details": res},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{change_id}/reject", response_model=ProposalActionResultResponse)
async def reject_proposal(
    change_id: UUID, current_user: UserProfileDTO = Depends(requires_permission(TASK_READ_TEAM))
) -> ProposalActionResultResponse:
    """Rejects the proposal. Requires Manager level visibility."""
    service = ProposeChangeService()
    try:
        res = await service.reject_proposal(change_id, user_id=current_user.id)
        return cast(
            ProposalActionResultResponse,
            {"status": "rejected", "message": "Change proposal rejected", "details": res},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
