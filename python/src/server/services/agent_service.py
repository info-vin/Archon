# python/src/server/services/agent_service.py

import asyncio

from ..config.logfire_config import get_logger
from .credential_service import credential_service
from .llm_provider_service import get_llm_client
from .shared_constants import AI_AGENT_ROLES  # Import AI_AGENT_ROLES from new shared module


class AgentService:
    """Service for handling business logic related to AI agents."""

    async def _analyze_error_and_suggest_fix(self, command: str, stderr: str) -> str:
        """
        Uses LLM to analyze the error output and suggest a fix.
        """
        logger = get_logger(__name__)
        prompt = f"""
You are an expert software engineer and debugger. The following shell command failed:

Command: `{command}`

Error Output (stderr):
{stderr}

Analyze the error and provide a concise explanation of what went wrong and a suggested fix.
If the error is a test failure, suggest how to fix the code.
If it's an environment issue, suggest how to fix the environment.
"""
        try:
            # Get active model from config
            provider_config = await credential_service.get_active_provider()
            model = provider_config.get("chat_model") or "gpt-4o"

            async with get_llm_client() as client:
                response = await client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.1
                )
                return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Failed to analyze error with LLM: {e}")
            return "Error analysis failed due to LLM provider issue."

    async def run_command_with_self_healing(self, command: str, max_retries: int = 1) -> tuple[bool, str]:
        """
        Executes a shell command with self-healing capabilities.
        If the command fails, it uses an LLM to analyze the error.

        Args:
            command: The shell command to execute.
            max_retries: Number of retries (currently used to limit analysis loop).
                         In a full implementation, this would loop and apply fixes.
                         For Phase 5 task 2, we focus on the analysis feedback loop.

        Returns:
            (success, output_or_analysis)
        """
        logger = get_logger(__name__)
        logger.info(f"Executing command with self-healing: {command}")

        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        stdout_str = stdout.decode().strip()
        stderr_str = stderr.decode().strip()

        if process.returncode == 0:
            logger.info(f"Command '{command}' succeeded.")
            return True, stdout_str

        logger.warning(f"Command '{command}' failed with exit code {process.returncode}.")

        # Self-healing logic: Analyze error
        analysis = await self._analyze_error_and_suggest_fix(command, stderr_str[-2000:]) # Pass last 2000 chars

        log_message = (
            f"Self-Healing Analysis for '{command}':\n"
            f"Error: {stderr_str[-500:]}...\n" # Log truncated error
            f"AI Suggestion: {analysis}"
        )
        logger.info(log_message)

        return False, log_message

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
            success, output_or_analysis = await self.run_command_with_self_healing(command)
            
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
