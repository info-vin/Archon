import asyncio
import logging
from pathlib import Path
from typing import Any, NotRequired, TypedDict, cast
from uuid import UUID

import aiofiles
from supabase import Client

from ..repositories.base_repository import BaseRepository


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

        # 2. Modify the file
        file_path = Path(str(file_path_str))
        async with aiofiles.open(file_path, "w") as f:
            await f.write(str(new_content))

        return f"Changes applied to branch {branch_name}"


class ProposeChangeService(BaseRepository):
    """Handles the lifecycle of proposed changes from AI or users."""

    def __init__(self, db_client: Client | None = None) -> None:
        super().__init__(db_client)
        self.db_client = self.supabase_client
        self.executor = ActionExecutor()
        self.logger = logging.getLogger(__name__)

    def _resolve_user_id(self, user_id: str | UUID | None) -> str | None:
        """Centralized check: ensure only strings are passed to Supabase"""
        if user_id is None:
            return None
        if isinstance(user_id, UUID):
            return str(user_id)
        if hasattr(user_id, "id"):
            # Some dependencies accidentally pass a user object
            return str(user_id.id)
        return str(user_id)

    async def list_proposals(self, status: str | None = "pending", user_id: str | None = None) -> list[ProposedChangeDict]:
        """List proposals based on status and optionally filtered by creator."""
        query = self.db_client.table("proposed_changes").select("*")
        if status:
            query = query.eq("status", status)
        # Physical Department Isolation (Phase 4.6.23 Hardening)
        if user_id:
            user_str = self._resolve_user_id(user_id)
            if user_str:
                p_success, p_res = await self.execute_query_async(self.db_client.table("profiles").select("department, role").eq("id", user_str), "Fetch profile")
                if p_success and p_res.get("data") and len(p_res["data"]) > 0:
                    profile = p_res["data"][0]
                    if profile.get("role") != "system_admin":
                        dept = profile.get("department")
                        query = query.filter("request_payload->>created_by_dept", "eq", dept)

        query = query.order("created_at", desc=True)
        success, response = await self.execute_query_async(query, "Failed to list proposals")

        return cast(list[ProposedChangeDict], response.get("data", []) if success else [])

    async def get_proposal(self, proposal_id: UUID) -> ProposedChangeDict | None:
        success, response = await self.execute_query_async(self.db_client.table("proposed_changes").select("*").eq("id", str(proposal_id)), "Get proposal")
        if not success or not response.get("data"):
            return None
        return cast(ProposedChangeDict, response["data"][0])

    async def create_file_proposal(
        self,
        file_path: str,
        new_content: str,
        summary: str,
        user_id: str | UUID | None = None,
    ) -> ProposedChangeDict:
        """Creates a file change proposal, capturing current content as old_content."""
        p = Path(file_path)
        old_content = ""
        if p.exists() and p.is_file():
            async with aiofiles.open(p, encoding="utf-8") as f:
                old_content = await f.read()

        user_str = self._resolve_user_id(user_id)
        dept = "General"
        if user_str:
            try:
                s, u_res = await self.execute_query_async(self.db_client.table("profiles").select("department").eq("id", user_str), "Get user dept")
                if s and u_res.get("data"):
                    dept = u_res["data"][0].get("department", "General")
            except Exception:
                pass

        payload: FileChangePayloadDict = {
            "file_path": file_path,
            "old_content": old_content,
            "new_content": new_content,
            "created_by": user_str,
            "created_by_dept": dept,
            "change_summary": summary,
        }

        return await self.create_proposal(
            change_type="file",
            payload=payload,
            user_id=user_str,
        )

    async def create_proposal(
        self,
        change_type: str,
        payload: dict[str, Any] | FileChangePayloadDict,
        user_id: str | None = None,
    ) -> ProposedChangeDict:
        """Creates a generic proposal (e.g. git commands, feature management) in proposed_changes."""
        dept = "General"
        if user_id:
            try:
                s, u_res = await self.execute_query_async(self.db_client.table("profiles").select("department").eq("id", user_id), "Get user dept")
                if s and u_res.get("data"):
                    dept = u_res["data"][0].get("department", "General")
            except Exception:
                pass

        # Inject created_by and created_by_dept into request_payload for audit
        request_payload = {
            **payload,
            "created_by": user_id,
            "created_by_dept": dept,
        }

        data = {
            "type": change_type,
            "request_payload": request_payload,
            "status": "pending",
        }

        success, response = await self.execute_query_async(self.db_client.table("proposed_changes").insert(data), "Insert proposal")
        if not success or not response.get("data"):
            raise RuntimeError("Failed to insert proposal")

        self.logger.info(f"Created proposal {response['data'][0].get('id')} of type {change_type}")
        return cast(ProposedChangeDict, response["data"][0])

    async def approve_proposal(self, proposal_id: UUID, user_id: str | UUID | None = None) -> ProposedChangeDict:
        """Approve and execute a proposal."""
        user_str = self._resolve_user_id(user_id)

        # 1. Fetch proposal
        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal {proposal_id} not found")
        if proposal.get("status") != "pending":
            raise ValueError(f"Proposal is already {proposal.get('status')}")

        # 2. Update DB with success
        success_data = {
            "status": "approved",
            "approved_by": user_str,
            "approved_at": "now()",
        }
        success, response = await self.execute_query_async(self.db_client.table("proposed_changes").update(success_data).eq("id", str(proposal_id)), "Approve proposal")

        # 3. Execute
        if success and response.get("data"):
            proposal_data = response["data"][0]
            try:
                await self.executor.execute_file_change(
                    payload=proposal_data.get("request_payload", {}), task_id=str(proposal_id)[:8]
                )
            except Exception as e:
                self.logger.error(f"Failed to execute approved change: {e}")
                raise

        # 4. Audit log
        try:
            user_name = "Unknown Admin"
            if user_str:
                s, u_res = await self.execute_query_async(self.db_client.table("profiles").select("name").eq("id", str(user_str)), "Get user name")
                if s and u_res.get("data"):
                    user_name = u_res["data"][0].get("name", "Unknown Admin")
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

        self.logger.info(f"Proposal {proposal_id} approved by {user_str}")
        return cast(ProposedChangeDict, response["data"][0])

    async def reject_proposal(self, proposal_id: UUID, user_id: str | UUID | None = None) -> ProposedChangeDict:
        """Reject a proposal without executing."""
        user_str = self._resolve_user_id(user_id)

        data = {
            "status": "rejected",
            "approved_by": user_str,
            "approved_at": "now()",
        }

        success, response = await self.execute_query_async(self.db_client.table("proposed_changes").update(data).eq("id", str(proposal_id)), "Reject proposal")
        if not success or not response.get("data"):
            raise RuntimeError(f"Failed to reject proposal {proposal_id}")

        # Audit log
        try:
            user_name = "Unknown Admin"
            if user_str:
                s, u_res = await self.execute_query_async(self.db_client.table("profiles").select("name").eq("id", str(user_str)), "Get user name")
                if s and u_res.get("data"):
                    user_name = u_res["data"][0].get("name", "Unknown Admin")
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

        self.logger.info(f"Proposal {proposal_id} rejected by {user_str}")
        return cast(ProposedChangeDict, response["data"][0])
