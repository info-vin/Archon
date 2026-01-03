# python/src/mcp_server/features/developer/version_control_tools.py
import asyncio
import logging

from pydantic import BaseModel, Field

from .....server.services.credential_service import credential_service
from .....server.services.llm_provider_service import get_llm_client

# Using the same dependency injector pattern as file_operation_tools
from .file_operation_tools import ToolDependencies

logger = logging.getLogger(__name__)

async def _get_staged_diff() -> str:
    """Gets the diff of staged changes."""
    try:
        # Check if git is available and we are in a git repo
        process = await asyncio.create_subprocess_exec(
            'git', 'diff', '--staged',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode != 0:
            logger.warning(f"Failed to get git diff: {stderr.decode()}")
            return ""
        return stdout.decode()
    except Exception as e:
        logger.warning(f"Error executing git diff: {e}")
        return ""

async def _generate_commit_message(diff: str, original_message: str) -> str:
    """Generates a smart commit message using LLM."""
    if not diff.strip():
        return original_message

    prompt = f"""
You are a senior software engineer. Generate a concise and semantic commit message following the Conventional Commits specification based on the provided git diff.

The user provided a generic message: "{original_message}"
Please improve it to be more descriptive based on the code changes.

Git Diff:
{diff[:8000]}  # Truncate to avoid context limit issues

Instructions:
1. Use the format: <type>(<scope>): <subject>
2. Keep the subject line under 72 characters.
3. If the diff is too complex, focus on the primary change.
4. ONLY return the commit message string, no markdown, no quotes, no explanations.
"""
    try:
        # Get active model from config
        provider_config = await credential_service.get_active_provider()
        model = provider_config.get("chat_model") or "gpt-4o"

        async with get_llm_client() as client:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.3
            )
            generated_message = response.choices[0].message.content.strip()
            # Remove any surrounding quotes if present
            if (generated_message.startswith('"') and generated_message.endswith('"')) or \
               (generated_message.startswith("'") and generated_message.endswith("'")):
                generated_message = generated_message[1:-1]

            logger.info(f"Smart Commit: Replaced '{original_message}' with '{generated_message}'")
            return generated_message

    except Exception as e:
        logger.error(f"Failed to generate smart commit message: {e}")
        return original_message

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

            final_message = self.commit_message

            # Smart Commit Logic: Improve generic messages
            generic_messages = ["update code", "update", "fix", "changes", "wip", "commit"]
            if self.commit_message.lower().strip() in generic_messages or len(self.commit_message.split()) < 3:
                logger.info("Generic commit message detected. Attempting to generate a smart commit message...")
                diff = await _get_staged_diff()
                if diff:
                    final_message = await _generate_commit_message(diff, self.commit_message)

            service = ToolDependencies.get_propose_change_service()
            payload = {
                "command": "git_commit",
                "commit_message": final_message,
                "description": f"Propose to commit staged changes with message: '{final_message}'."
            }
            proposal = await service.create_proposal(change_type='git', payload=payload)

            return (f"Successfully proposed a git commit. "
                    f"Proposal ID: {proposal['id']}. Please await human approval.\n"
                    f"Message: {final_message}")
        except Exception as e:
            logger.error(f"Failed to propose git commit: {e}", exc_info=True)
            return f"Error: Could not propose git commit. Reason: {e}"

# To be added to the MCP's tool registry
developer_version_control_tools = [
    ProposeGitBranchTool,
    ProposeGitCommitTool,
]
