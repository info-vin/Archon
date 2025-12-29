# python/src/server/services/propose_change_service.py

import logging
import os
import subprocess
from typing import Any

from supabase_py_async import AsyncClient

from ..utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)

# A whitelist of commands that the AI is allowed to propose for execution.
# This is a critical security measure.
WHITELISTED_SHELL_COMMANDS = [
    "git",
    "ls",
    "cat",
    "make",
    "npm",
    "pnpm",
    "ruff",
    "pytest",
    "uv",
    "node",
]


class ProposeChangeService:
    """
    Service to manage the lifecycle of proposed changes.
    It handles creation, approval, rejection, and execution of proposals.
    """

    def __init__(self):
        self.supabase: AsyncClient = get_supabase_client()

    async def create_proposal(
        self, user_id: str, proposal_type: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        """Creates a new change proposal in the database."""
        logger.info(
            f"Creating proposal of type '{proposal_type}' for user '{user_id}'"
        )
        response = (
            await self.supabase.table("proposed_changes")
            .insert(
                {
                    "user_id": user_id,
                    "type": proposal_type,
                    "request_payload": payload,
                    "status": "pending",
                }
            )
            .execute()
        )
        if not response.data:
            raise Exception("Failed to create proposal in database.")
        return response.data[0]

    async def get_proposal(self, change_id: str) -> dict[str, Any] | None:
        """Retrieves a single proposal by its ID."""
        response = (
            await self.supabase.table("proposed_changes")
            .select("*")
            .eq("id", change_id)
            .maybe_single()
            .execute()
        )
        return response.data

    async def list_proposals(self, status: str = "pending") -> list[dict[str, Any]]:
        """Lists all proposals, optionally filtered by status."""
        response = (
            await self.supabase.table("proposed_changes")
            .select("*")
            .eq("status", status)
            .order("created_at", desc=True)
            .execute()
        )
        return response.data

    async def approve_proposal(
        self, change_id: str, approver_id: str
    ) -> dict[str, Any]:
        """Approves a proposal and triggers its execution."""
        logger.info(f"Approving proposal '{change_id}' by user '{approver_id}'")
        proposal = await self.get_proposal(change_id)
        if not proposal:
            raise ValueError(f"Proposal with id '{change_id}' not found.")
        if proposal["status"] != "pending":
            raise ValueError("Only pending proposals can be approved.")

        # Update status to approved first
        await self.supabase.table("proposed_changes").update(
            {"status": "approved"}
        ).eq("id", change_id).execute()

        try:
            await self._execute_approved_proposal(proposal)
            # If execution succeeds, update status to executed
            logger.info(f"Proposal '{change_id}' executed successfully.")
            response = (
                await self.supabase.table("proposed_changes")
                .update({"status": "executed"})
                .eq("id", change_id)
                .execute()
            )
            return response.data[0]
        except Exception as e:
            logger.error(
                f"Execution failed for proposal '{change_id}': {e}", exc_info=True
            )
            # If execution fails, update status to failed
            response = (
                await self.supabase.table("proposed_changes")
                .update({"status": "failed", "result_payload": {"error": str(e)}})
                .eq("id", change_id)
                .execute()
            )
            # Re-raise the exception to inform the caller
            raise e

    async def reject_proposal(
        self, change_id: str, rejector_id: str
    ) -> dict[str, Any]:
        """Rejects a proposal."""
        logger.info(f"Rejecting proposal '{change_id}' by user '{rejector_id}'")
        response = (
            await self.supabase.table("proposed_changes")
            .update({"status": "rejected"})
            .eq("id", change_id)
            .execute()
        )
        if not response.data:
            raise ValueError(f"Proposal with id '{change_id}' not found or could not be updated.")
        return response.data[0]

    async def _execute_approved_proposal(self, proposal: dict[str, Any]) -> None:
        """
        Executes the action defined in the proposal.
        This is a critical function and must handle actions securely.
        """
        proposal_type = proposal.get("type")
        payload = proposal.get("request_payload", {})

        match proposal_type:
            case "file_write":
                filepath = payload.get("filepath")
                content = payload.get("content")
                if not filepath or content is None:
                    raise ValueError("Filepath and content are required for 'file_write'.")
                # Basic security: prevent path traversal
                if ".." in filepath:
                    raise PermissionError("File path cannot contain '..'.")

                safe_path = os.path.abspath(os.path.join(os.getcwd(), filepath))
                if not safe_path.startswith(os.getcwd()):
                     raise PermissionError("Attempted to write file outside of the project directory.")

                with open(safe_path, "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info(f"Successfully wrote to file: {safe_path}")

            case "git_checkout":
                branch_name = payload.get("branch_name")
                if not branch_name:
                    raise ValueError("Branch name is required for 'git_checkout'.")
                # Security: Sanitize branch name
                # A simple check for now, can be improved.
                if not branch_name.isalnum() and "-" not in branch_name and "_" not in branch_name:
                    raise ValueError("Branch name contains invalid characters.")

                result = subprocess.run(
                    ["git", "checkout", "-b", branch_name],
                    capture_output=True, text=True, check=False
                )
                if result.returncode != 0:
                    raise RuntimeError(f"Git checkout failed: {result.stderr}")
                logger.info(f"Successfully checked out new branch: {branch_name}")

            case "shell_command":
                command = payload.get("command")
                args = payload.get("args", [])
                if not command:
                    raise ValueError("Command is required for 'shell_command'.")
                if command not in WHITELISTED_SHELL_COMMANDS:
                    raise PermissionError(f"Command '{command}' is not in the whitelist.")

                full_command = [command] + args
                result = subprocess.run(
                    full_command, capture_output=True, text=True, check=False
                )
                if result.returncode != 0:
                    raise RuntimeError(f"Shell command failed: {result.stderr}")
                logger.info(f"Successfully executed: {' '.join(full_command)}. Output: {result.stdout}")

            case _:
                raise NotImplementedError(f"Proposal type '{proposal_type}' is not supported.")
