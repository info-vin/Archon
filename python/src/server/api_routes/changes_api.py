# python/src/server/api_routes/changes_api.py

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..services.propose_change_service import ProposeChangeService
from ..services.rbac_service import User, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()
propose_change_service = ProposeChangeService()


class CreateProposalRequest(BaseModel):
    proposal_type: str
    payload: dict


class ChangeProposal(BaseModel):
    id: str
    status: str
    type: str
    request_payload: dict
    user_id: str | None
    created_at: str
    updated_at: str

    class Config:
        orm_mode = True


@router.post(
    "/api/changes",
    response_model=ChangeProposal,
    tags=["Changes"],
    summary="Create a new change proposal",
    status_code=status.HTTP_201_CREATED,
)
async def create_change_proposal(
    request: CreateProposalRequest, user: User = Depends(get_current_user)
):
    """
    Creates a new change proposal for review.
    This endpoint is typically called by an AI agent.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        proposal = await propose_change_service.create_proposal(
            user_id=user.id,
            proposal_type=request.proposal_type,
            payload=request.payload,
        )
        return proposal
    except Exception as e:
        logger.error(f"Error creating proposal: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create proposal.",
        ) from e


@router.get(
    "/api/changes",
    response_model=list[ChangeProposal],
    tags=["Changes"],
    summary="List change proposals",
)
async def list_change_proposals(
    status: str = "pending", user: User = Depends(get_current_user)
):
    """
    Retrieves a list of change proposals, filtered by status.
    Defaults to 'pending' status. Requires authentication.
    """
    # Basic authorization: for now, any authenticated user can list.
    # This could be expanded with more granular permissions.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        proposals = await propose_change_service.list_proposals(status=status)
        return proposals
    except Exception as e:
        logger.error(f"Error listing proposals: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve proposals.",
        ) from e


@router.get(
    "/api/changes/{change_id}",
    response_model=ChangeProposal,
    tags=["Changes"],
    summary="Get a single change proposal",
)
async def get_change_proposal(change_id: str, user: User = Depends(get_current_user)):
    """
    Retrieves a single change proposal by its ID.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    proposal = await propose_change_service.get_proposal(change_id)
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Proposal with id '{change_id}' not found.",
        )
    return proposal


@router.post(
    "/api/changes/{change_id}/approve",
    response_model=ChangeProposal,
    tags=["Changes"],
    summary="Approve and execute a change proposal",
)
async def approve_change_proposal(
    change_id: str, user: User = Depends(get_current_user)
):
    """
    Approves a pending change proposal, which triggers its execution.
    Requires appropriate permissions.
    """
    # For now, let's assume any authenticated user can approve.
    # In a real scenario, this would check for 'admin' or 'reviewer' roles.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        approved_proposal = await propose_change_service.approve_proposal(
            change_id=change_id, approver_id=user.id
        )
        return approved_proposal
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error approving proposal '{change_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve proposal: {e}",
        ) from e


@router.post(
    "/api/changes/{change_id}/reject",
    response_model=ChangeProposal,
    tags=["Changes"],
    summary="Reject a change proposal",
)
async def reject_change_proposal(
    change_id: str, user: User = Depends(get_current_user)
):
    """
    Rejects a pending change proposal.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
        )
    try:
        rejected_proposal = await propose_change_service.reject_proposal(
            change_id=change_id, rejector_id=user.id
        )
        return rejected_proposal
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error rejecting proposal '{change_id}': {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject proposal.",
        ) from e
