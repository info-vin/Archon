# python/src/server/services/propose_change_service.py
import asyncio
import logging
from pathlib import Path
from typing import Any, NotRequired, TypedDict, cast
from uuid import UUID

import aiofiles

from ..utils import get_supabase_client


class FileChangePayloadDict(TypedDict):
    file_path: NotRequired[str]
    old_content: NotRequired[str]
    new_content: NotRequired[str]
    created_by: NotRequired[str | None]
    created_by_dept: NotRequired[str]
    change_summary: NotRequired[str]


class ProposedChangeDict(TypedDict):
    id: NotRequired[str]
    created_at: NotRequired[str]
    status: NotRequired[str]
    type: NotRequired[str]
    request_payload: NotRequired[FileChangePayloadDict | dict[str, Any]]
    approved_by: NotRequired[str | None]
    approved_at: NotRequired[str | None]
    executed_at: NotRequired[str | None]
    execution_log: NotRequired[str | None]


class ActionExecutor:
    """Handles the actual execution of an approved change."""

    async def _run_command(self, *args: str) -> str:
        process = await asyncio.create_subprocess_exec(
            *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logging.error(f"Command failed: {stderr.decode().strip()}")
            raise RuntimeError("Command failed")
        return stdout.decode().strip()

    async def execute_file_change(self, payload: FileChangePayloadDict | dict[str, Any], task_id: str = "ai-fix") -> str:
        file_path_str = payload.get("file_path")
        new_content = payload.get("new_content")

        if not file_path_str or new_content is None:
            raise ValueError("Invalid payload")

        from ..utils.code_modifier import CodeModifier

        modifier = CodeModifier()

        # 1. Create a sandbox branch for safety
        branch_name = modifier.create_sandbox_branch(task_id)

        # 2. Apply the modification
        modifier.apply_modification(file_path_str, new_content)

        return f"File '{file_path_str}' written to branch '{branch_name}'"


class ProposeChangeService:
    def __init__(self, db_client: Any | None = None) -> None:
        self.db_client = db_client or get_supabase_client()
        from ..repositories.base_repository import BaseRepository
        self.base_repo = BaseRepository(self.db_client)
        self.executor = ActionExecutor()
        self.logger = logging.getLogger(__name__)

    def _resolve_user_id(self, user_id: Any) -> str:
        """
        Dynamically handles both UUIDs and simplified IDs ('1', '2', '3').
        Ensures the ID is returned in a format suitable for the database column.
        """
        uid_str = str(user_id)
        # If it's a simple numeric string, we treat it as a valid identity
        # but keep it as a string to match the updated TEXT column type.
        return uid_str

    async def list_proposals(self, status: str | None = "pending", user_id: str | None = None) -> list[ProposedChangeDict]:
        """Lists proposals, optionally filtered by status and user department scope."""
        query = self.db_client.table("proposed_changes").select("*") # 合法
        if status:
            query = query.eq("status", status)

        # Physical Department Isolation (Phase 4.6.23 Hardening)
        if user_id:
            # First, get the department of the requesting manager
            success, p_res = self.base_repo.execute_query(
                self.db_client.table("profiles").select("department, role").eq("id", user_id), # 合法
                error_context="Failed to query profiles"
            )
            if success and p_res.get("data") and len(p_res["data"]) > 0:
                profile = p_res["data"][0]
                if profile.get("role") != "system_admin":
                    dept = profile.get("department")
                    query = query.filter("request_payload->>created_by_dept", "eq", dept)

        success, res = self.base_repo.execute_query(
            query.order("created_at", desc=True),
            error_context="Failed to list proposals"
        )
        return cast(list[ProposedChangeDict], res.get("data", []) if success else [])

    async def get_proposal(self, proposal_id: UUID) -> ProposedChangeDict | None:
        success, res = self.base_repo.execute_query(
            self.db_client.table("proposed_changes").select("*").eq("id", str(proposal_id)), # 合法
            error_context="Failed to get proposal"
        )
        return res["data"][0] if success and res.get("data") else None

    async def create_file_proposal(
        self, file_path: str, new_content: str, summary: str, user_id: str | None = None
    ) -> ProposedChangeDict:
        """Creates a file change proposal, capturing current content as old_content."""
        p = Path(file_path)
        old_content = ""
        if p.exists() and p.is_file():
            async with aiofiles.open(p, encoding="utf-8") as f:
                old_content = await f.read()

        # Physical identity embedding (Phase 4.6.23)
        dept = "General"
        if user_id:
            success, u_res = self.base_repo.execute_query(
                self.db_client.table("profiles").select("department").eq("id", user_id), # 合法
                error_context="Failed to query profiles"
            )
            dept = u_res["data"][0].get("department", "General") if success and u_res.get("data") else "General"

        payload = {
            "file_path": file_path,
            "old_content": old_content,
            "new_content": new_content,
            "created_by": user_id,
            "created_by_dept": dept,
            "change_summary": summary,
        }

        success, res = self.base_repo.execute_query(
            self.db_client.table("proposed_changes") # 合法
            .insert({"type": "file", "status": "pending", "request_payload": payload}),
            error_context="Failed to create file proposal"
        )
        return cast(ProposedChangeDict, res["data"][0])

    async def create_proposal(
        self, change_type: str, payload: dict[str, Any], user_id: str | None = None
    ) -> ProposedChangeDict:
        """Creates a generic proposal (e.g. git commands, feature management) in proposed_changes."""
        # Embed physical identity (Phase 4.6.23)
        dept = "General"
        if user_id:
            success, u_res = self.base_repo.execute_query(
                self.db_client.table("profiles").select("department").eq("id", user_id), # 合法
                error_context="Failed to query profiles"
            )
            dept = u_res["data"][0].get("department", "General") if success and u_res.get("data") else "General"

        # Inject created_by and created_by_dept into request_payload for audit
        request_payload = {
            **payload,
            "created_by": user_id,
            "created_by_dept": dept,
        }

        success, res = self.base_repo.execute_query(
            self.db_client.table("proposed_changes") # 合法
            .insert({"type": change_type, "status": "pending", "request_payload": request_payload}),
            error_context="Failed to create proposal"
        )
        return cast(ProposedChangeDict, res["data"][0])

    async def approve_proposal(self, proposal_id: UUID, user_id: Any) -> ProposedChangeDict:
        resolved_id = self._resolve_user_id(user_id)
        success, res = self.base_repo.execute_query(
            self.db_client.table("proposed_changes") # 合法
            .update({"status": "approved", "approved_by": resolved_id, "approved_at": "now()"})
            .eq("id", str(proposal_id)),
            error_context="Failed to approve proposal"
        )

        # Physical Execution Trigger (Phase 5.1.3)
        if success and res.get("data"):
            proposal = res["data"][0]
            try:
                await self.executor.execute_file_change(
                    proposal.get("request_payload", {}), task_id=str(proposal_id)[:8]
                )
            except Exception as e:
                self.logger.error(f"Failed to execute approved change: {e}")
                raise

        # Physical Audit Log (Phase 4.6.41)
        try:
            success, u_res = self.base_repo.execute_query(
                self.db_client.table("profiles").select("name").eq("id", str(user_id)), # 合法
                error_context="Failed to query profile for audit"
            )
            user_name = u_res["data"][0].get("name", "Unknown Admin") if success and u_res.get("data") else "Unknown Admin"

            from .log_service import log_service

            log_service.create_log_entry(
                {
                    "project_name": "admin-audit",
                    "user_name": user_name,
                    "gemini_response": f"Proposal {proposal_id} approved by {user_name}",
                    "user_input": f"Approve {proposal_id}",
                }
            )
        except Exception as e:
            self.logger.warning(f"Audit log failed: {e}")

        return cast(ProposedChangeDict, res["data"][0])

    async def reject_proposal(self, proposal_id: UUID, user_id: Any) -> ProposedChangeDict:
        resolved_id = self._resolve_user_id(user_id)
        success, res = self.base_repo.execute_query(
            self.db_client.table("proposed_changes") # 合法
            .update({"status": "rejected", "approved_by": resolved_id, "approved_at": "now()"})
            .eq("id", str(proposal_id)),
            error_context="Failed to reject proposal"
        )

        # Physical Audit Log (Phase 4.6.41)
        try:
            success, u_res = self.base_repo.execute_query(
                self.db_client.table("profiles").select("name").eq("id", str(user_id)), # 合法
                error_context="Failed to query profile for audit"
            )
            user_name = u_res["data"][0].get("name", "Unknown Admin") if success and u_res.get("data") else "Unknown Admin"

            from .log_service import log_service

            log_service.create_log_entry(
                {
                    "project_name": "admin-audit",
                    "user_name": user_name,
                    "gemini_response": f"Proposal {proposal_id} rejected by {user_name}",
                    "user_input": f"Reject {proposal_id}",
                }
            )
        except Exception as e:
            self.logger.warning(f"Audit log failed: {e}")

        return cast(ProposedChangeDict, res["data"][0])
