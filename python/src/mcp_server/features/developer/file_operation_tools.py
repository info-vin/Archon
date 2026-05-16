# python/src/mcp_server/features/developer/file_operation_tools.py
import logging

from pydantic import BaseModel, Field

# This is a placeholder for the actual service.
# In a real implementation, this would be injected.
from src.server.services.propose_change_service import ProposeChangeService

logger = logging.getLogger(__name__)


# A mock dependency injector for now
class ToolDependencies:
    _propose_change_service: ProposeChangeService = None

    @classmethod
    def get_propose_change_service(cls) -> ProposeChangeService:
        if cls._propose_change_service is None:
            # In a real app, this would be properly initialized and injected.
            # For now, we create a mock/placeholder.
            from src.server.dependencies import get_supabase_client

            db_client = get_supabase_client()
            cls._propose_change_service = ProposeChangeService(db_client=db_client)
        return cls._propose_change_service


class ProposeFileChangeTool(BaseModel):
    """
    Proposes a change to a file by writing new content to it.
    This action does not write the file directly but submits a change proposal
    for human review.
    """

    file_path: str = Field(..., description="The full path of the file to be modified.")
    new_content: str = Field(..., description="The new content to be written to the file.")

    async def execute(self) -> str:
        """Submits the file change proposal."""
        logger.info(f"Proposing a change to file: {self.file_path}")
        try:
            service = ToolDependencies.get_propose_change_service()
            summary = f"Agent Update: {self.file_path.split('/')[-1]}"

            proposal = await service.create_file_proposal(
                file_path=self.file_path, new_content=self.new_content, summary=summary
            )

            return (
                f"Successfully proposed a change to file '{self.file_path}'. "
                f"Proposal ID: {proposal['id']}. Please await human approval."
            )
        except Exception as e:
            logger.error(f"Failed to propose file change for {self.file_path}: {e}", exc_info=True)
            return f"Error: Could not propose change for file '{self.file_path}'. Reason: {e}"


# We can also have a simpler tool name for the AI to use
class WriteFileTool(ProposeFileChangeTool):
    """Alias for ProposeFileChangeTool."""

    pass


class ApplyFileModificationTool(BaseModel):
    """
    Physically modifies a file by overwriting it with new content.
    WARNING: This action is destructive and writes directly to disk.
    Used for automated self-healing and code updates.
    """

    tool_name: str = "apply_modification"
    file_path: str = Field(..., description="The relative path of the file to be modified (from workspace root).")
    content: str = Field(..., description="The full new content to be written to the file.")

    async def execute(self) -> str:
        """Physically modifies the file by direct write (no Git sandbox)."""
        logger.info(f"Applying physical modification to file: {self.file_path}")
        try:
            import os
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)

            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(self.content)

            return f"Successfully modified file '{self.file_path}' physically via direct write."
        except Exception as e:
            logger.error(f"Failed to modify file {self.file_path}: {e}", exc_info=True)
            return f"Error: Could not modify file '{self.file_path}'. Reason: {e}"


# To be added to the MCP's tool registry
developer_file_tools: list[type[BaseModel]] = [
    ProposeFileChangeTool,
    WriteFileTool,
    ApplyFileModificationTool,
]
