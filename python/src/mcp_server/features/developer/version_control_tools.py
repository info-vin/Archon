# python/src/mcp_server/features/developer/version_control_tools.py
import logging

from pydantic import BaseModel, Field

# Using the same dependency injector pattern as file_operation_tools
from .file_operation_tools import ToolDependencies

logger = logging.getLogger(__name__)

class ProposeGitBranchTool(BaseModel):
    """
    Proposes the creation of a new Git branch.
    This action requires human approval before the branch is actually created.
    """
    branch_name: str = Field(..., description="The name of the new branch to create (e.g., 'feature/new-login-flow').")

    async def execute(self) -> str:
        """Submits the git branch creation proposal."""
        logger.info(f"Proposing to create a new git branch: {self.branch_name}")
        try:
            # Basic validation
            if not self.branch_name or " " in self.branch_name:
                return "Error: Invalid branch name. It cannot be empty or contain spaces."

            service = ToolDependencies.get_propose_change_service()
            payload = {
                "command": "git_create_branch",
                "branch_name": self.branch_name,
                "description": f"Propose to create a new branch named '{self.branch_name}'."
            }
            proposal = await service.create_proposal(change_type='git', payload=payload)

            return (f"Successfully proposed to create a new branch '{self.branch_name}'. "
                    f"Proposal ID: {proposal['id']}. Please await human approval.")
        except Exception as e:
            logger.error(f"Failed to propose git branch '{self.branch_name}': {e}", exc_info=True)
            return f"Error: Could not propose git branch creation. Reason: {e}"

class ProposeGitCommitTool(BaseModel):
    """
    Proposes committing all currently staged changes to the current branch.
    This action requires human approval before the commit is made.
    """
    commit_message: str = Field(..., description="The commit message (e.g., 'feat: Add user authentication endpoint').")

    async def execute(self) -> str:
        """Submits the git commit proposal."""
        logger.info(f"Proposing a git commit with message: {self.commit_message}")
        try:
            if not self.commit_message:
                return "Error: Commit message cannot be empty."

            service = ToolDependencies.get_propose_change_service()
            payload = {
                "command": "git_commit",
                "commit_message": self.commit_message,
                "description": f"Propose to commit staged changes with message: '{self.commit_message}'."
            }
            proposal = await service.create_proposal(change_type='git', payload=payload)

            return (f"Successfully proposed a git commit. "
                    f"Proposal ID: {proposal['id']}. Please await human approval.")
        except Exception as e:
            logger.error(f"Failed to propose git commit: {e}", exc_info=True)
            return f"Error: Could not propose git commit. Reason: {e}"

# To be added to the MCP's tool registry
developer_version_control_tools = [
    ProposeGitBranchTool,
    ProposeGitCommitTool,
]
