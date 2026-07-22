"""
Agent Approval Manager for Phase 5.9.13 (HITL Workflow).

Manages pending human approval requests for sensitive Agent tool calls.
"""

import logging
from dataclasses import dataclass
from typing import Any

from src.server.utils import get_supabase_client

logger = logging.getLogger(__name__)


@dataclass
class ApprovalRequestDTO:
    conversation_id: str
    checkpoint_id: str
    tool_name: str
    tool_args: dict[str, Any]
    risk_level: str = "HIGH"
    status: str = "PENDING"
    approval_id: str | None = None
    reviewer_id: str | None = None
    review_reason: str | None = None
    created_at: str | None = None
    expires_at: str | None = None


class AgentApprovalManager:
    """Manages Human-in-the-Loop (HITL) tool approval requests and statuses."""

    def __init__(self, supabase_client=None) -> None:
        self.supabase = supabase_client if supabase_client is not None else get_supabase_client()

    async def create_approval_request(self, dto: ApprovalRequestDTO) -> str:
        """Creates a new pending approval record in Supabase."""
        payload = {
            "conversation_id": dto.conversation_id,
            "checkpoint_id": dto.checkpoint_id,
            "tool_name": dto.tool_name,
            "tool_args": dto.tool_args,
            "risk_level": dto.risk_level,
            "status": "PENDING",
        }
        res = self.supabase.table("agent_pending_approvals").insert(payload).execute()
        if res.data:
            approval_id = str(res.data[0]["approval_id"])
            logger.info(f"[ApprovalManager] Created HITL approval request {approval_id} for tool '{dto.tool_name}'")
            return approval_id
        raise RuntimeError("Failed to create pending approval request")

    async def list_pending_approvals(self) -> list[ApprovalRequestDTO]:
        """Lists all active PENDING approval requests."""
        res = (
            self.supabase.table("agent_pending_approvals")
            .select("*")
            .eq("status", "PENDING")
            .order("created_at", desc=True)
            .execute()
        )
        return [
            ApprovalRequestDTO(
                approval_id=d.get("approval_id"),
                conversation_id=d["conversation_id"],
                checkpoint_id=d["checkpoint_id"],
                tool_name=d["tool_name"],
                tool_args=d["tool_args"],
                risk_level=d.get("risk_level", "HIGH"),
                status=d["status"],
                reviewer_id=d.get("reviewer_id"),
                review_reason=d.get("review_reason"),
                created_at=d.get("created_at"),
                expires_at=d.get("expires_at"),
            )
            for d in res.data or []
        ]

    async def review_approval(
        self, approval_id: str, approved: bool, reviewer_id: str = "admin", reason: str | None = None
    ) -> ApprovalRequestDTO:
        """Approves or rejects a pending tool execution request."""
        new_status = "APPROVED" if approved else "REJECTED"
        payload = {
            "status": new_status,
            "reviewer_id": reviewer_id,
            "review_reason": reason or ("Approved by reviewer" if approved else "Rejected by reviewer"),
        }
        res = (
            self.supabase.table("agent_pending_approvals")
            .update(payload)
            .eq("approval_id", approval_id)
            .execute()
        )
        if not res.data:
            raise ValueError(f"Approval request {approval_id} not found")

        d = res.data[0]
        # Also update associated checkpoint status
        checkpoint_status = "RUNNING" if approved else "CANCELLED"
        self.supabase.table("agent_checkpoints").update({"status": checkpoint_status}).eq("id", d["checkpoint_id"]).execute()

        logger.info(f"[ApprovalManager] Approval {approval_id} reviewed as {new_status} by {reviewer_id}")
        return ApprovalRequestDTO(
            approval_id=d["approval_id"],
            conversation_id=d["conversation_id"],
            checkpoint_id=d["checkpoint_id"],
            tool_name=d["tool_name"],
            tool_args=d["tool_args"],
            risk_level=d.get("risk_level", "HIGH"),
            status=d["status"],
            reviewer_id=d.get("reviewer_id"),
            review_reason=d.get("review_reason"),
            created_at=d.get("created_at"),
            expires_at=d.get("expires_at"),
        )
