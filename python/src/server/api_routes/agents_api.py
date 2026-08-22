
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.server.models.agent_models import (
    AgentCheckpointResponse,
    ApprovalRequestResponse,
    ResumeExecutionResult,
    ReviewApprovalResponse,
)
from src.server.models.auth_models import UserProfileDTO

from ..auth.dependencies import get_current_user
from ..config.logfire_config import get_logger
from ..services.agent_service import AgentService, agent_service

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/agents",
    tags=["agents"],
)


@router.get("/health")
async def agents_health() -> Any:
    """
    Health check for the AI agents service.
    """
    return {"status": "healthy", "service": "agents"}


@router.get("/assignable", response_model=list[dict])
async def get_assignable_agents(
    current_user: UserProfileDTO = Depends(get_current_user), service: AgentService = Depends(lambda: agent_service)
):
    """
    Get a list of all assignable AI agents.
    Filtered by user role (RBAC).
    """
    try:
        user_role = current_user.role
        agents = await service.get_assignable_agents(user_role=user_role)
        return agents
    except Exception as e:
        logger.error(f"Failed to get assignable agents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve assignable agents") from e


# Phase 5.9.13: Agent DB State Checkpointing & HITL Endpoints

@router.get("/approvals/pending", response_model=list[ApprovalRequestResponse])
async def get_pending_approvals() -> list[ApprovalRequestResponse]:
    """
    Get all active PENDING human approval requests for sensitive agent tool calls.
    """
    try:
        from src.agents.approval_manager import AgentApprovalManager
        mgr = AgentApprovalManager()
        approvals = await mgr.list_pending_approvals()
        return [
            {
                "approval_id": a.approval_id,
                "conversation_id": a.conversation_id,
                "checkpoint_id": a.checkpoint_id,
                "tool_name": a.tool_name,
                "tool_args": a.tool_args,
                "risk_level": a.risk_level,
                "status": a.status,
                "created_at": a.created_at,
                "expires_at": a.expires_at,
            }
            for a in approvals
        ]
    except Exception as e:
        logger.error(f"Failed to get pending approvals: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending approvals") from e


@router.post("/approvals/{approval_id}/review", response_model=ReviewApprovalResponse)
async def review_approval(approval_id: str, approved: bool, reason: str | None = None, current_user: UserProfileDTO = Depends(get_current_user)) -> ReviewApprovalResponse:
    """
    Approve or reject a pending sensitive tool execution.
    """
    try:
        from src.agents.approval_manager import AgentApprovalManager
        mgr = AgentApprovalManager()
        reviewer_id = current_user.id
        res = await mgr.review_approval(approval_id=approval_id, approved=approved, reviewer_id=reviewer_id, reason=reason)
        return {
            "success": True,
            "approval_id": res.approval_id,
            "status": res.status,
            "message": f"Approval {approval_id} successfully marked as {res.status}.",
        }
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as e:
        logger.error(f"Failed to review approval {approval_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to process approval review") from e


@router.post("/tasks/{conversation_id}/resume", response_model=ResumeExecutionResult)
async def resume_agent_task(conversation_id: str) -> ResumeExecutionResult:
    """
    Resume an agent task execution from its latest checkpoint.
    """
    try:
        from src.agents.execution_engine import AgentExecutionEngine
        engine = AgentExecutionEngine()
        res = await engine.resume_execution(conversation_id=conversation_id)
        return res
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve)) from ve
    except Exception as e:
        logger.error(f"Failed to resume agent task {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume agent task") from e


@router.get("/checkpoints/{conversation_id}", response_model=list[AgentCheckpointResponse])
async def list_agent_checkpoints(conversation_id: str) -> list[AgentCheckpointResponse]:
    """
    Get all state checkpoints for a given agent conversation.
    """
    try:
        from src.agents.checkpoint_manager import AgentCheckpointManager
        mgr = AgentCheckpointManager()
        checkpoints = await mgr.list_checkpoints(conversation_id=conversation_id)
        return [
            {
                "id": c.id,
                "conversation_id": c.conversation_id,
                "step_index": c.step_index,
                "agent_role": c.agent_role,
                "status": c.status,
                "state_snapshot": c.state_snapshot,
                "last_tool_call": c.last_tool_call,
                "created_at": c.created_at,
            }
            for c in checkpoints
        ]
    except Exception as e:
        logger.error(f"Failed to get checkpoints for {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent checkpoints") from e

