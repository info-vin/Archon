# python/src/server/api_routes/changes_api.py
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_current_user_id, get_propose_change_service
from ..services.propose_change_service import ProposeChangeService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/changes", tags=["Changes"])
async def list_pending_changes(
    propose_change_service: ProposeChangeService = Depends(get_propose_change_service)
):
    """
    Lists all proposed changes with 'pending' status.
    In a real application, this should be paginated.
    """
    try:
        # TODO: Add RBAC to ensure only authorized users can view proposals
        proposals = await propose_change_service.list_proposals(status='pending')
        return proposals
    except Exception as e:
        logger.error(f"Error listing pending changes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve proposed changes.") from e

@router.get("/changes/{change_id}", tags=["Changes"])
async def get_change_details(
    change_id: UUID,
    propose_change_service: ProposeChangeService = Depends(get_propose_change_service)
):
    """
    Gets the detailed information for a single proposed change.
    """
    try:
        # TODO: Add RBAC to ensure user is authorized to view this specific proposal
        proposal = await propose_change_service.get_proposal(change_id)
        if not proposal:
            raise HTTPException(status_code=404, detail="Proposed change not found.")
        return proposal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting change details for {change_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve change details.") from e

@router.post("/changes/{change_id}/approve", tags=["Changes"])
async def approve_and_execute_change(
    change_id: UUID,
    propose_change_service: ProposeChangeService = Depends(get_propose_change_service),
    current_user_id: UUID = Depends(get_current_user_id) # Placeholder for auth
):
    """
    Approves a proposed change and triggers its execution.
    This is the core of the human-in-the-loop workflow.
    """
    try:
        # TODO: Implement strict RBAC. Only users with a 'manager' or 'admin' role
        # should be allowed to call this endpoint.

        # 1. Approve the proposal
        await propose_change_service.approve_proposal(proposal_id=change_id, user_id=current_user_id)

        # 2. Execute the proposal
        # In a real-world scenario, execution might be a background task.
        # For simplicity, we do it directly here.
        executed_proposal = await propose_change_service.execute_proposal(proposal_id=change_id)

        return executed_proposal
    except (ValueError, PermissionError) as e:
        logger.warning(f"Failed to approve/execute change {change_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Error during approval/execution of change {change_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred during the approval process.") from e

@router.post("/changes/{change_id}/reject", tags=["Changes"])
async def reject_change(
    change_id: UUID,
    propose_change_service: ProposeChangeService = Depends(get_propose_change_service),
    current_user_id: UUID = Depends(get_current_user_id) # Auth check
):
    """
    Rejects a proposed change.
    """
    try:
        # TODO: Implement strict RBAC.
        rejected_proposal = await propose_change_service.reject_proposal(
            proposal_id=change_id,
            user_id=current_user_id
        )
        return rejected_proposal
    except Exception as e:
        logger.error(f"Error rejecting change {change_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to reject proposed change.") from e
