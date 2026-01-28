# python/src/server/services/agent_service.py

import asyncio
import json
import uuid

from ..config.logfire_config import get_logger

# Import the new CodeModifier utility
from ..utils.code_modifier import CodeModifier
from .credential_service import credential_service
from .llm_provider_service import get_llm_client
from .shared_constants import AI_AGENT_ROLES


class AgentService:
    """Service for handling business logic related to AI agents."""

    def __init__(self):
        self.code_modifier = CodeModifier(base_path=".")

    async def _analyze_error_with_structured_output(self, command: str, stderr: str) -> dict | None:
        """
        Uses LLM to analyze the error output and suggest a fix in structured JSON.
        Returns:
            {
                "file_path": "path/to/file",
                "fixed_content": "new file content",
                "reasoning": "explanation"
            }
            OR None if analysis fails or no fix is possible.
        """
        logger = get_logger(__name__)
        prompt = f"""
You are an expert software engineer and debugger. The following shell command failed:

Command: `{command}`

Error Output (stderr):
{stderr}

Analyze the error. If it is a fixable code error (e.g., SyntaxError, TypeScript error, logic bug), provide a fix.
You MUST return a JSON object with the following structure:
{{
    "file_path": "The relative path of the file to fix (e.g., 'scripts/foo.py')",
    "fixed_content": "The COMPLETE content of the fixed file (do not use diffs)",
    "reasoning": "A brief explanation of the fix"
}}

If the error is an environment issue or you cannot fix it by modifying code, return an empty JSON object {{}}.
Ensure the "fixed_content" is valid code for the target language.
"""
        try:
            # Get active model from config
            provider_config = await credential_service.get_active_provider()
            model = provider_config.get("chat_model") or "gpt-4o"

            async with get_llm_client() as client:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4000, # Increased for full file content
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                content = response.choices[0].message.content.strip()
                if not content:
                    return None
                return json.loads(content)
        except Exception as e:
            logger.error(f"Failed to analyze error with LLM: {e}")
            return None

    async def run_command_with_self_healing(self, command: str, max_retries: int = 1, task_id: str = None) -> tuple[bool, str]:
        """
        Executes a shell command with self-healing capabilities (DevBot L2).
        Loop: Execute -> Fail -> Analyze -> Sandbox -> Apply -> Verify -> Success/Fail
        """
        logger = get_logger(__name__)
        # Generate a temporary task ID if not provided, for branch naming
        if not task_id:
            task_id = f"auto-{uuid.uuid4().hex[:8]}"

        logger.info(f"Executing command with self-healing (L2): {command}")

        # --- Attempt 1: Initial Execution ---
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        if process.returncode == 0:
            logger.info(f"Command '{command}' succeeded initially.")
            return True, stdout_str

        logger.warning(f"Command '{command}' failed. Starting Active Repair Loop.")

        # --- Active Repair Loop ---
        # 1. Analyze
        fix_proposal = await self._analyze_error_with_structured_output(command, stderr_str[-2000:])

        if not fix_proposal or not fix_proposal.get("file_path") or not fix_proposal.get("fixed_content"):
            logger.warning("LLM could not propose a valid code fix.")
            return False, f"Command failed. Analysis: {fix_proposal.get('reasoning') if fix_proposal else 'No analysis available'}.\nStderr: {stderr_str}"

        # 2. Sandbox
        original_branch = self.code_modifier.get_current_branch()
        try:
            sandbox_branch = self.code_modifier.create_sandbox_branch(task_id)
        except Exception as e:
            return False, f"Failed to create sandbox: {e}"

        # 3. Apply Fix
        try:
            self.code_modifier.apply_modification(
                fix_proposal["file_path"],
                fix_proposal["fixed_content"]
            )
            logger.info(f"Applied fix to {fix_proposal['file_path']} on branch {sandbox_branch}")
        except Exception as e:
            self.code_modifier.revert_sandbox(original_branch)
            return False, f"Failed to apply fix: {e}"

        # 4. Verify (Retry Command)
        logger.info(f"Verifying fix by re-running: {command}")
        process_retry = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout_retry, stderr_retry = await process_retry.communicate()

        if process_retry.returncode == 0:
            logger.info(f"Fix verified! Task completed on branch {sandbox_branch}.")
            msg = (
                f"### Command Succeeded after Auto-Repair\n"
                f"**Fix Logic**: {fix_proposal.get('reasoning')}\n"
                f"**Sandbox Branch**: `{sandbox_branch}`\n"
                f"**Action Required**: Please review the branch and merge via PR."
            )
            # Important: We stay on the sandbox branch so the user can see the result?
            # Or should we revert? The instructions say "Handover happens via ProposeChangeService".
            # For this MVP, we leave the branch checked out for the user to inspect.
            return True, msg
        else:
            logger.warning("Fix verification failed. Reverting sandbox.")
            self.code_modifier.revert_sandbox(original_branch)
            return False, f"Auto-repair failed verification. Stderr: {stderr_retry.decode().strip()[-500:]}"

    async def get_assignable_agents(self) -> list[dict]:
        """
        Retrieves a list of assignable AI agents.
        """
        assignable_agents = []
        for role_name, agent_id in AI_AGENT_ROLES.items():
            assignable_agents.append({"id": agent_id, "name": role_name, "role": role_name})
        return assignable_agents

    async def run_agent_task(self, task_id: str, agent_id: str, command: str | None = None):
        """
        Runs a task by an AI agent with self-healing feedback loop.
        """
        # Local import to break circular dependency
        from ..services.projects.task_service import task_service

        logger = get_logger(__name__)
        logger.info(f"AI agent '{agent_id}' starting work on task '{task_id}'.")

        # 1. Update status to processing
        success, result = await task_service.update_task(
            task_id, {"status": "processing", "assignee": agent_id}
        )
        if not success:
            logger.error(f"Failed to update task status: {result.get('error')}")
            return

        # 2. Execute command with self-healing if provided
        if command:
            # Pass task_id for branching
            success, output_or_analysis = await self.run_command_with_self_healing(command, task_id=task_id)

            # 3. Feed the results back into the task output/description
            final_status = "done" if success else "failed"
            update_data = {
                "status": final_status,
                "output": output_or_analysis
            }

            # If failed, we keep it in 'failed' status but provide the AI analysis
            # as a hint for the next manual or automated retry.
            await task_service.update_task(task_id, update_data)
            logger.info(f"Task '{task_id}' finished with status '{final_status}'. Output/Analysis provided.")
        else:
            # Fallback for tasks without explicit shell commands (simulated work)
            await asyncio.sleep(1)
            await task_service.update_task(task_id, {"status": "done", "output": "Simulated task completed successfully."})
            logger.info(f"AI agent '{agent_id}' finished simulated work for task '{task_id}'.")

# Create a singleton instance of the service
agent_service = AgentService()
