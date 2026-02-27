# python/src/server/services/propose_change_service.py
import asyncio
import logging
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import aiofiles  # type: ignore

from ..utils import get_supabase_client


class ActionExecutor:
    """Handles the actual execution of an approved change."""
    async def _run_command(self, *args: str) -> str:
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logging.error(f"Command failed: {stderr.decode().strip()}")
            raise RuntimeError("Command failed")
        return stdout.decode().strip()

    async def execute_file_change(self, payload: dict[str, Any]) -> str:
        file_path_str = payload.get('file_path')
        new_content = payload.get('new_content')

        if not file_path_str or new_content is None:
            raise ValueError("Invalid payload")

        file_path = Path(file_path_str)
        if not file_path.is_relative_to(Path.cwd()):
            raise PermissionError("Security: Path outside project")

        file_path.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(new_content)
        return f"File '{file_path}' written"

class ProposeChangeService:
    def __init__(self, db_client=None):
        self.db_client = db_client or get_supabase_client()
        self.executor = ActionExecutor()
        self.logger = logging.getLogger(__name__)

    async def list_proposals(self, status: str | None = 'pending') -> list[dict[str, Any]]:
        query = self.db_client.table("proposed_changes").select("*")
        if status:
            query = query.eq("status", status)
        res = query.order("created_at", desc=True).execute()
        return cast(list[dict[str, Any]], res.data or [])

    async def get_proposal(self, proposal_id: UUID) -> dict[str, Any] | None:
        res = self.db_client.table("proposed_changes").select("*").eq("id", str(proposal_id)).execute()
        return res.data[0] if res.data else None

    async def create_file_proposal(self, file_path: str, new_content: str, summary: str) -> dict[str, Any]:
        """Creates a file change proposal, capturing current content as old_content."""
        p = Path(file_path)
        old_content = ""
        if p.exists() and p.is_file():
            async with aiofiles.open(p, 'r', encoding='utf-8') as f:
                old_content = await f.read()
        
        payload = {
            "file_path": file_path,
            "old_content": old_content,
            "new_content": new_content
        }
        
        res = self.db_client.table("proposed_changes").insert({
            "type": "file",
            "status": "pending",
            "change_summary": summary,
            "request_payload": payload
        }).execute()
        return cast(dict[str, Any], res.data[0])

    async def approve_proposal(self, proposal_id: UUID, user_id: Any) -> dict[str, Any]:
        res = self.db_client.table("proposed_changes").update({"status": "approved", "approved_by": str(user_id), "approved_at": "now()"}).eq("id", str(proposal_id)).execute()
        return cast(dict[str, Any], res.data[0])

    async def reject_proposal(self, proposal_id: UUID, user_id: Any) -> dict[str, Any]:
        res = self.db_client.table("proposed_changes").update({"status": "rejected", "approved_by": str(user_id), "approved_at": "now()"}).eq("id", str(proposal_id)).execute()
        return cast(dict[str, Any], res.data[0])

    async def execute_proposal(self, proposal_id: UUID) -> dict[str, Any]:
        proposal = await self.get_proposal(proposal_id)
        if not proposal or proposal['status'] != 'approved':
            raise PermissionError("Not approved")
        try:
            change_type, payload = proposal['type'], proposal['request_payload']
            log = await self.executor.execute_file_change(payload) if change_type == 'file' else "Executed"
            res = self.db_client.table("proposed_changes").update({"status": "executed", "executed_at": "now()", "execution_log": log}).eq("id", str(proposal_id)).execute()
            return cast(dict[str, Any], res.data[0])
        except Exception as e:
            self.db_client.table("proposed_changes").update({"status": "failed", "execution_log": str(e)}).eq("id", str(proposal_id)).execute()
            raise
