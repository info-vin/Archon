"""
Agent Checkpoint Manager for Phase 5.9.13.

Provides DB-backed state persistence for long-running Agent tasks using Supabase.
"""

import logging
from dataclasses import dataclass
from typing import Any

from src.server.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


@dataclass
class CheckpointDTO:
    conversation_id: str
    step_index: int
    agent_role: str
    status: str
    state_snapshot: dict[str, Any]
    last_tool_call: dict[str, Any] | None = None
    id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class AgentCheckpointManager(BaseRepository):
    """Manages saving, reading, and restoring Agent state checkpoints in Supabase."""

    def __init__(self, supabase_client=None) -> None:
        super().__init__(supabase_client=supabase_client)

    async def save_checkpoint(self, dto: CheckpointDTO) -> str:
        """Saves or updates a state checkpoint snapshot in the database."""
        payload = {
            "conversation_id": dto.conversation_id,
            "step_index": dto.step_index,
            "agent_role": dto.agent_role,
            "status": dto.status,
            "state_snapshot": dto.state_snapshot,
            "last_tool_call": dto.last_tool_call,
        }
        query = self.supabase_client.table("agent_checkpoints").upsert(payload, on_conflict="conversation_id,step_index")
        success, res = self.execute_query(query, "Failed to save agent checkpoint to database")
        if success and res.get("data"):
            checkpoint_id = str(res["data"][0]["id"])
            logger.info(f"[CheckpointManager] Saved checkpoint {checkpoint_id} for conv {dto.conversation_id} step {dto.step_index}")
            return checkpoint_id
        raise RuntimeError("Failed to save agent checkpoint to database")

    async def load_latest_checkpoint(self, conversation_id: str) -> CheckpointDTO | None:
        """Loads the most recent checkpoint for a given conversation ID."""
        query = (
            self.supabase_client.table("agent_checkpoints")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("step_index", desc=True)
            .limit(1)
        )
        success, res = self.execute_query(query, f"Failed to load latest checkpoint for conv {conversation_id}")
        if not success or not res.get("data"):
            return None
        d = res["data"][0]
        return CheckpointDTO(
            id=d.get("id"),
            conversation_id=d["conversation_id"],
            step_index=d["step_index"],
            agent_role=d["agent_role"],
            status=d["status"],
            state_snapshot=d["state_snapshot"],
            last_tool_call=d.get("last_tool_call"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
        )

    async def list_checkpoints(self, conversation_id: str) -> list[CheckpointDTO]:
        """Lists all checkpoints for a conversation in chronological order."""
        query = (
            self.supabase_client.table("agent_checkpoints")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("step_index", desc=False)
        )
        success, res = self.execute_query(query, f"Failed to list checkpoints for conv {conversation_id}")
        data = res.get("data", []) if success else []
        return [
            CheckpointDTO(
                id=d.get("id"),
                conversation_id=d["conversation_id"],
                step_index=d["step_index"],
                agent_role=d["agent_role"],
                status=d["status"],
                state_snapshot=d["state_snapshot"],
                last_tool_call=d.get("last_tool_call"),
                created_at=d.get("created_at"),
                updated_at=d.get("updated_at"),
            )
            for d in data
        ]
