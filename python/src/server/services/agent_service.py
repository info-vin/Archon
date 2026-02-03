# python/src/server/services/agent_service.py

import asyncio
import json
import uuid
from typing import Any, cast

from ..config.logfire_config import get_logger
from ..prompts.dev_ops_prompts import DEVBOT_TOOLS, get_devbot_analysis_prompt

# Import the new CodeModifier utility
from ..utils.code_modifier import CodeModifier
from .agent_registry import get_agent_config
from .credential_service import credential_service
from .llm_provider_service import get_llm_client
from .shared_constants import AI_AGENT_ROLES


class AgentService:
    """Service for handling business logic related to AI agents."""

    def __init__(self, mcp_client=None):
        self.code_modifier = CodeModifier(base_path=".")
        self.mcp_client = mcp_client



    async def _handle_tool_calls(self, tool_calls) -> list[dict]:
        """
        Executes tool calls requested by the LLM via MCP client or Local Services.
        """
        logger = get_logger(__name__)
        tool_outputs = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            call_id = tool_call.id

            logger.info(f"[MCP] Agent requesting tool execution: {function_name} | args={arguments}")

            try:
                result = "Tool execution failed (Unknown)"

                # --- Routing Logic ---

                # 1. Code Modification (Local Service)
                if function_name == "apply_modification":
                    # For MVP, we apply directly. Phase 5 adds PR flow.
                    file_path = arguments.get("file_path")
                    content = arguments.get("content")
                    if not file_path or not content:
                        raise ValueError("Missing file_path or content")

                    self.code_modifier.apply_modification(file_path, content)
                    result = f"Successfully modified {file_path}"

                # 2. Code Search (Local)
                # TODO: Wire to RAGService or Grep?
                # For now, let's assuming MCP handles it or we mock it if missing
                elif function_name == "search_code_examples":
                     # Redirect to MCP if available, or simple error
                     if self.mcp_client:
                         if hasattr(self.mcp_client, function_name):
                             result = await getattr(self.mcp_client, function_name)(**arguments)
                         else:
                             result = await self.mcp_client.call_tool(function_name, **arguments)
                     else:
                         result = "Search not available (No MCP)"

                # 3. Default MCP Pass-through
                elif self.mcp_client:
                    if hasattr(self.mcp_client, function_name):
                        method = getattr(self.mcp_client, function_name)
                        result = await method(**arguments)
                    else:
                        result = await self.mcp_client.call_tool(function_name, **arguments)

                else:
                    raise Exception("MCP Client not initialized and no local handler found")

                tool_outputs.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": str(result)
                })

            except Exception as e:
                logger.error(f"[MCP] Tool execution failed ({function_name}): {e}")
                tool_outputs.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "content": f"Error executing tool '{function_name}': {str(e)}"
                })

        return tool_outputs

    async def _analyze_error_with_structured_output(self, command: str, stderr: str) -> dict[str, Any] | None:
        """
        Uses LLM to analyze the error output and suggest a fix in structured JSON.
        Supports L2+ Capability: Uses MCP tools (RAG/Search) to research before fixing.
        """
        logger = get_logger(__name__)
        prompt = get_devbot_analysis_prompt(command, stderr)

        # Prepare messages
        messages = [{"role": "user", "content": prompt}]

        # Determine if we can use tools
        tools = DEVBOT_TOOLS if self.mcp_client else None

        try:
            # Get active model from config
            provider_config = await credential_service.get_active_provider()
            model = provider_config.get("chat_model") or "gpt-4o"

            async with get_llm_client() as client:
                # --- Round 1: Analysis & Potential Tool Call ---
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto" if tools else None,
                    max_tokens=4000,
                    temperature=0.1,
                    # We don't enforce json_object yet because it might call a tool
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                # Case A: LLM wants to use tools (Look-Before-Leap)
                if tool_calls and self.mcp_client:
                    logger.info(f"DevBot triggered {len(tool_calls)} tool calls for research.")

                    # Append assistant's intent to history
                    messages.append(response_message)

                    # Execute tools
                    tool_outputs = await self._handle_tool_calls(tool_calls)
                    messages.extend(tool_outputs)

                    # --- Round 2: Final Verdict with Context ---
                    # Now we force JSON output for the final fix proposal
                    final_response = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        max_tokens=4000,
                        temperature=0.1,
                        response_format={"type": "json_object"}
                    )
                    content = final_response.choices[0].message.content.strip()

                # Case B: LLM replied directly (Direct Fix)
                else:
                    content = response_message.content.strip()
                    # If it's not JSON (because we didn't enforce it in R1), we might need to retry or parsing might fail
                    # But usually for "auto", if it doesn't call tools, it follows the prompt instructions.
                    # To be safe, let's ensure it's JSON.
                    # Optimization: In Round 1, if we didn't force JSON, we might get text.
                    # Ideally, we should check if content starts with '{'.

                if not content:
                    return None

                # Parse JSON
                try:
                    return cast(dict[str, Any], json.loads(content))
                except json.JSONDecodeError:
                    # Fallback: Try to find JSON block if LLM was chatty
                    import re
                    match = re.search(r'\{.*\}', content, re.DOTALL)
                    if match:
                        return cast(dict[str, Any], json.loads(match.group(0)))
                    return None

        except Exception as e:
            logger.error(f"Failed to analyze error with LLM: {e}")
            return None

    async def run_command_with_self_healing(self, command: str, max_retries: int = 1, task_id: str | None = None) -> tuple[bool, str]:
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

    async def get_assignable_agents(self, user_role: str | None = None) -> list[dict]:
        """
        Retrieves a list of assignable AI agents, filtered by user role.
        RBAC Policy:
        - Admin/Manager: All agents
        - Sales: MarketBot only
        - Marketing: MarketBot + Librarian
        """
        all_agents: list[dict[str, Any]] = []
        for role_name, agent_id in AI_AGENT_ROLES.items():
            # Initialize with all keys to ensure MyPy infers correct dict types
            all_agents.append({
                "id": agent_id,
                "name": role_name,
                "role": role_name,
                "tools": [],
                "description": "AI Agent"
            })

        if not user_role or user_role in ["admin", "system_admin", "manager"]:
            return all_agents

        filtered_agents = []

        # RBAC Filtering Logic (SSOT from Matrix)
        for agent in all_agents:
            agent_id = agent["id"]

            # Enrich with capabilities from Registry
            config = get_agent_config(agent_id)
            if config:
                agent["tools"] = config.get("tools", [])
                # Use first line of system prompt or a hardcoded desc as description
                prompt = config.get("system_prompt", "")
                agent["description"] = prompt.split("\n")[0] if prompt else "AI Agent"
            else:
                agent["tools"] = []
                agent["description"] = "AI Agent"

            if user_role == "sales":
                # Alice sees only MarketBot
                if agent_id == "ai-market-bot":
                    filtered_agents.append(agent)

            elif user_role == "marketing":
                # Bob sees MarketBot + Librarian
                if agent_id in ["ai-market-bot", "ai-librarian"]:
                    filtered_agents.append(agent)

            # Admin/Manager sees all (implicit in "else")
            else:
                filtered_agents.append(agent)

        return filtered_agents

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

        # 2. Execute command with self-healing if provided (DevBot Mode)
        if command:
            # Pass task_id for branching
            success, output_or_analysis = await self.run_command_with_self_healing(command, task_id=task_id)
            final_status = "done" if success else "failed"
            await task_service.update_task(task_id, {"status": final_status, "output": output_or_analysis})

        # 3. Wake up other bots (General Agent Mode)
        else:
            await self._run_general_agent_task(task_id, agent_id)

    async def _run_general_agent_task(self, task_id: str, agent_id: str):
        """
        Executes a non-command task using the General MCP Agent Loop.
        Applies to MarketBot, Librarian, POBot, etc.
        """
        from ..services.projects.task_service import task_service
        logger = get_logger(__name__)

        # 1. Get Agent Configuration
        config = get_agent_config(agent_id)
        if not config:
            logger.error(f"Agent '{agent_id}' not found in registry. Failing task.")
            await task_service.update_task(task_id, {"status": "failed", "output": f"Unknown agent: {agent_id}"})
            return

        # 2. Fetch Task Details
        success, task_data = await task_service.get_task(task_id)
        if not success or not task_data:
            logger.error(f"Failed to fetch task {task_id}")
            return

        user_input = f"Task: {task_data['title']}\nDescription: {task_data.get('description', 'No description provided.')}"

        # 3. Initialize Loop Context
        messages = [
            {"role": "system", "content": config["system_prompt"]},
            {"role": "user", "content": user_input}
        ]

        # Determine available tools
        # For simplicity, we define basic tool skeletons here based on the registry.
        # Ideally, we should import these from dev_ops_prompts or similar.
        all_mcp_tools: list[dict[str, Any]] = [
            {"type": "function", "function": {"name": "search_job_market", "description": "Find jobs on 104/LinkedIn.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "generate_sales_email", "description": "Write a sales email.", "parameters": {"type": "object", "properties": {"company": {"type": "string"}, "pitch": {"type": "string"}}, "required": ["company", "pitch"]}}},
            {"type": "function", "function": {"name": "perform_rag_query", "description": "Search knowledge base.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "get_available_sources", "description": "List indexed docs.", "parameters": {"type": "object", "properties": {}}}},
            {"type": "function", "function": {"name": "manage_task", "description": "Create/Update tasks.", "parameters": {"type": "object", "properties": {"action": {"type": "string", "enum": ["create", "update", "delete"]}, "task_id": {"type": "string"}}, "required": ["action"]}}},
            # DevBot Tools
            {"type": "function", "function": {"name": "search_code_examples", "description": "Search codebase.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "apply_modification", "description": "Modify a file.", "parameters": {"type": "object", "properties": {"file_path": {"type": "string"}, "content": {"type": "string"}}, "required": ["file_path", "content"]}}},
            {"type": "function", "function": {"name": "generate_logo", "description": "Generate SVG.", "parameters": {"type": "object", "properties": {"prompt": {"type": "string"}}, "required": ["prompt"]}}}
        ]

        # Filter tools owned by this agent
        agent_tools_list = config.get("tools", [])
        agent_tools = [t for t in all_mcp_tools if t["function"]["name"] in agent_tools_list]
        tools_param = agent_tools if (agent_tools and self.mcp_client) else None

        try:
            provider_config = await credential_service.get_active_provider()
            model = provider_config.get("chat_model") or "gpt-4o"

            async with get_llm_client() as client:
                # --- Round 1: Thinking ---
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=tools_param,
                    tool_choice="auto" if tools_param else None,
                    temperature=0.3
                )

                res_msg = response.choices[0].message
                tool_calls = res_msg.tool_calls

                # --- Round 2: Action (Optional) ---
                if tool_calls and self.mcp_client:
                    logger.info(f"Agent '{agent_id}' is performing {len(tool_calls)} actions...")
                    messages.append(res_msg)
                    tool_results = await self._handle_tool_calls(tool_calls)
                    messages.extend(tool_results)

                    # Get final answer after tool execution
                    final_response = await client.chat.completions.create(
                        model=model,
                        messages=messages
                    )
                    final_output = final_response.choices[0].message.content
                else:
                    final_output = res_msg.content

                # 4. Finalize Task
                await task_service.update_task(task_id, {
                    "status": "done",
                    "output": final_output or "Task completed with no text output."
                })
                logger.info(f"Task {task_id} completed by {agent_id}.")

        except Exception as e:
            logger.error(f"Agent Loop Failed: {e}")
            await task_service.update_task(task_id, {"status": "failed", "output": f"Error: {str(e)}"})


# Create a singleton instance of the service
agent_service = AgentService()
