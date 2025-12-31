# python/src/mcp_server/features/developer/execution_tools.py
import logging

from pydantic import BaseModel, Field

# Using the same dependency injector pattern
from .file_operation_tools import ToolDependencies

logger = logging.getLogger(__name__)

# A whitelist of commands that are considered safe to be proposed.
# The approval UI should strongly enforce this.
SAFE_COMMAND_WHITELIST = [
    "make test-be",
    "make test",
    "make lint-be",
    "make lint",
    # Specific pytest commands could be allowed if necessary
    # "uv run pytest python/tests/server/api_routes/test_changes_api.py"
]


class ProposeShellCommandTool(BaseModel):
    """
    Proposes running a shell command from a pre-approved whitelist.
    This is a high-risk operation that requires human approval. Only commands
    from a known safe list (like 'make test-be') should ever be approved.
    """
    command: str = Field(..., description=f"The shell command to propose. Must be one of: {', '.join(SAFE_COMMAND_WHITELIST)}")

    async def execute(self) -> str:
        """Submits the shell command execution proposal."""
        logger.info(f"Proposing to execute a shell command: {self.command}")

        # --- Crucial Security Check ---
        # The tool itself should validate against the whitelist before even proposing.
        if self.command not in SAFE_COMMAND_WHITELIST:
            logger.warning(f"Blocked attempt to propose a non-whitelisted command: {self.command}")
            return (f"Error: The command '{self.command}' is not in the list of "
                    f"approved safe commands. Proposal rejected.")

        try:
            service = ToolDependencies.get_propose_change_service()
            payload = {
                "command": self.command,
                "description": f"Propose to run the shell command: `{self.command}`."
            }
            proposal = await service.create_proposal(change_type='shell', payload=payload)

            return (f"Successfully proposed to run the command: `{self.command}`. "
                    f"Proposal ID: {proposal['id']}. Please await human approval.")
        except Exception as e:
            logger.error(f"Failed to propose shell command '{self.command}': {e}", exc_info=True)
            return f"Error: Could not propose shell command execution. Reason: {e}"

# To be added to the MCP's tool registry
developer_execution_tools = [
    ProposeShellCommandTool,
]
