# python/src/agents/developer_agent.py

import logging
import os
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext

from .base_agent import ArchonDependencies, BaseAgent
from .mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


@dataclass
class DeveloperDependencies(ArchonDependencies):
    """Dependencies for developer agent operations."""

    task_id: str | None = None


class DeveloperAgent(BaseAgent[DeveloperDependencies, str]):
    """
    An AI agent designed to act as a developer teammate.
    It can propose changes to the codebase, which must be approved by a human.
    """

    def __init__(self, model: str = None, **kwargs):
        if model is None:
            model = os.getenv("DEVELOPER_AGENT_MODEL", "openai:gpt-4o-mini")
        super().__init__(
            model=model, name="DeveloperAgent", retries=2, enable_rate_limiting=True, **kwargs
        )

    def _create_agent(self, **kwargs) -> Agent:
        agent = Agent(
            model=self.model,
            deps_type=DeveloperDependencies,
            system_prompt="""You are a Developer AI Teammate. Your goal is to complete coding tasks by proposing changes to the filesystem. You cannot execute changes directly; all your actions must be submitted for human review.

**Your Approach:**
1. **Understand the Goal:** Analyze the user's request.
2. **Explore:** Use tools like `list_files` or `read_file` (if available) to understand the current state of the code.
3. **Propose Changes:** Use the available tools (`propose_file_write`, `propose_git_checkout`, etc.) to submit your desired changes. You must provide clear reasons for each proposal.
4. **Report:** After proposing a change, clearly state what you have done and what the next step should be.
""",
            **kwargs,
        )

        @agent.tool
        async def propose_file_write(
            ctx: RunContext[DeveloperDependencies], filepath: str, content: str, reason: str
        ) -> str:
            """
            Proposes to write content to a file. The change will be submitted for human review.
            Provide a clear reason for the change.
            """
            try:
                mcp_client = await get_mcp_client()
                await mcp_client.create_change_proposal(
                    proposal_type="file_write",
                    payload={"filepath": filepath, "content": content, "reason": reason},
                )
                return f"Successfully proposed to write to '{filepath}'. Awaiting human review. Reason: {reason}"
            except Exception as e:
                logger.error(f"Error proposing file write to '{filepath}': {e}", exc_info=True)
                return f"Error: Could not propose file write. Details: {e}"

        @agent.tool
        async def propose_git_checkout(
            ctx: RunContext[DeveloperDependencies], branch_name: str, reason: str
        ) -> str:
            """
            Proposes to create and checkout a new git branch. The change will be submitted for human review.
            Provide a clear reason for this action.
            """
            try:
                mcp_client = await get_mcp_client()
                await mcp_client.create_change_proposal(
                    proposal_type="git_checkout",
                    payload={"branch_name": branch_name, "reason": reason},
                )
                return f"Successfully proposed to checkout new branch '{branch_name}'. Awaiting human review. Reason: {reason}"
            except Exception as e:
                logger.error(f"Error proposing git checkout for branch '{branch_name}': {e}", exc_info=True)
                return f"Error: Could not propose git checkout. Details: {e}"

        @agent.tool
        async def propose_shell_command(
            ctx: RunContext[DeveloperDependencies], command: str, args: list[str], reason: str
        ) -> str:
            """
            Proposes to run a shell command from a pre-approved whitelist. The change will be submitted for human review.
            Provide a clear reason for running the command.
            """
            try:
                mcp_client = await get_mcp_client()
                await mcp_client.create_change_proposal(
                    proposal_type="shell_command",
                    payload={"command": command, "args": args, "reason": reason},
                )
                return f"Successfully proposed to run command '{command} {' '.join(args)}'. Awaiting human review. Reason: {reason}"
            except Exception as e:
                logger.error(f"Error proposing shell command '{command}': {e}", exc_info=True)
                return f"Error: Could not propose shell command. Details: {e}"


        return agent

    async def run_task(self, user_message: str, task_id: str | None = None, user_id: str | None = None) -> str:
        """
        Run the developer agent to complete a task.
        """
        deps = DeveloperDependencies(task_id=task_id, user_id=user_id)
        try:
            response_text = await self.run(user_message, deps)
            return response_text
        except Exception as e:
            self.logger.error(f"Developer agent failed for task '{task_id}': {str(e)}", exc_info=True)
            return f"An error occurred while running the developer agent: {e}"
