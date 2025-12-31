# python/src/server/services/propose_change_service.py
import asyncio
import logging
from pathlib import Path
from typing import Any
from uuid import UUID

import aiofiles
from supabase_py_async import AsyncClient


# A placeholder for the actual execution logic
# In a real implementation, this would interact with file systems, git, etc.
class ActionExecutor:
    """
    Handles the actual execution of an approved change.
    This is separated to keep the ProposeChangeService focused on state management.
    """
    async def _run_command(self, *args: str) -> str:
        """Helper to run a shell command and return its output."""
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode().strip()
            logging.error(f"Command `{' '.join(args)}` failed: {error_message}")
            raise RuntimeError(f"Command execution failed: {error_message}")

        return stdout.decode().strip()

    async def execute_file_change(self, payload: dict[str, Any]) -> str:
        file_path_str = payload.get('file_path')
        new_content = payload.get('new_content')

        if not file_path_str or new_content is None:
            raise ValueError("Payload must contain 'file_path' and 'new_content'.")

        file_path = Path(file_path_str)
        # Security: ensure the path is within the project directory and not, e.g., /etc/passwd
        # This is a simplistic check. A real implementation should be more robust.
        if not file_path.is_relative_to(Path.cwd()):
             raise PermissionError(f"File path '{file_path}' is outside the allowed project directory.")

        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(new_content)

        return f"File '{file_path}' written successfully."

    async def execute_git_change(self, payload: dict[str, Any]) -> str:
        git_command = payload.get('command')
        if not git_command:
            raise ValueError("Git payload must contain a 'command'.")

        if git_command == 'git_create_branch':
            branch_name = payload.get('branch_name')
            if not branch_name:
                raise ValueError("Missing 'branch_name' for git_create_branch.")
            return await self._run_command('git', 'checkout', '-b', branch_name)

        elif git_command == 'git_commit':
            commit_message = payload.get('commit_message')
            if not commit_message:
                raise ValueError("Missing 'commit_message' for git_commit.")
            # Note: This assumes files are already staged. A more robust tool
            # would also handle staging files.
            return await self._run_command('git', 'commit', '-m', commit_message)

        else:
            raise ValueError(f"Unsupported git command: {git_command}")

    async def execute_shell_change(self, payload: dict[str, Any]) -> str:
        command_to_run = payload.get('command')
        if not command_to_run:
            raise ValueError("Shell payload must contain a 'command'.")

        # Security: The command has been whitelisted in the tool, but we could
        # double-check here if needed.
        # For simplicity, we trust the proposing layer.

        # We split the command to avoid `shell=True` which is a security risk.
        command_parts = command_to_run.split()
        return await self._run_command(*command_parts)


class ProposeChangeService:
    def __init__(self, db_client: AsyncClient):
        self.db_client = db_client
        self.executor = ActionExecutor()
        self.logger = logging.getLogger(__name__)

    async def create_proposal(self, change_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Creates a new proposed change and stores it in the database."""
        self.logger.info(f"Creating proposal of type '{change_type}' with payload: {payload}")

        response = await self.db_client.table("proposed_changes").insert({
            "type": change_type,
            "request_payload": payload,
            "status": "pending"
        }).execute()

        if not response.data:
            raise Exception("Failed to create proposal in database.")

        return response.data[0]

    async def list_proposals(self, status: str | None = 'pending') -> list[dict[str, Any]]:
        """Lists all proposals, optionally filtered by status."""
        self.logger.info(f"Listing proposals with status: {status}")

        query = self.db_client.table("proposed_changes").select("*")
        if status:
            query = query.eq("status", status)

        response = await query.order("created_at", desc=True).execute()

        return response.data

    async def get_proposal(self, proposal_id: UUID) -> dict[str, Any] | None:
        """Retrieves a single proposal by its ID."""
        self.logger.info(f"Getting proposal with ID: {proposal_id}")

        response = await self.db_client.table("proposed_changes").select("*").eq("id", proposal_id).maybe_single().execute()

        return response.data

    async def approve_proposal(self, proposal_id: UUID, user_id: UUID) -> dict[str, Any]:
        """Marks a proposal as approved."""
        self.logger.info(f"Approving proposal {proposal_id} by user {user_id}")

        response = await self.db_client.table("proposed_changes").update({
            "status": "approved",
            "approved_by": str(user_id),
            "approved_at": "now()"
        }).eq("id", proposal_id).select("*").execute()

        if not response.data:
            raise Exception(f"Proposal with ID {proposal_id} not found or could not be updated.")

        return response.data[0]

    async def reject_proposal(self, proposal_id: UUID, user_id: UUID) -> dict[str, Any]:
        """Marks a proposal as rejected."""
        self.logger.info(f"Rejecting proposal {proposal_id} by user {user_id}")

        response = await self.db_client.table("proposed_changes").update({
            "status": "rejected",
            "approved_by": str(user_id), # We can use the same field to track who rejected it
            "approved_at": "now()"
        }).eq("id", proposal_id).select("*").execute()

        if not response.data:
            raise Exception(f"Proposal with ID {proposal_id} not found or could not be updated.")

        return response.data[0]

    async def execute_proposal(self, proposal_id: UUID) -> dict[str, Any]:
        """Executes an approved proposal and updates its status."""
        self.logger.info(f"Executing proposal {proposal_id}")

        proposal = await self.get_proposal(proposal_id)
        if not proposal:
            raise ValueError(f"Proposal with ID {proposal_id} not found.")

        if proposal['status'] != 'approved':
            raise PermissionError(f"Proposal {proposal_id} is not in 'approved' state. Current state: {proposal['status']}")

        execution_log = ""
        try:
            change_type = proposal['type']
            payload = proposal['request_payload']

            if change_type == 'file':
                execution_log = await self.executor.execute_file_change(payload)
            elif change_type == 'git':
                execution_log = await self.executor.execute_git_change(payload)
            elif change_type == 'shell':
                execution_log = await self.executor.execute_shell_change(payload)
            else:
                raise ValueError(f"Unknown change type: {change_type}")

            # Update status to executed
            update_response = await self.db_client.table("proposed_changes").update({
                "status": "executed",
                "executed_at": "now()",
                "execution_log": execution_log
            }).eq("id", proposal_id).execute()

            return update_response.data[0]

        except Exception as e:
            self.logger.error(f"Execution failed for proposal {proposal_id}: {e}", exc_info=True)
            # Update status to failed
            await self.db_client.table("proposed_changes").update({
                "status": "failed",
                "execution_log": str(e)
            }).eq("id", proposal_id).execute()
            raise
