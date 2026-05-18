from __future__ import annotations

import logging
import os
from typing import Any, Literal

import httpx
import pydantic_ai
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from src.server.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)

# Version helper to handle PydanticAI breaking changes
PAI_V1 = not pydantic_ai.__version__.startswith("0.")

# --- 1. Shared State ---
class SharedState(BaseModel):
    messages: list[dict[str, Any]] = Field(default_factory=list)
    current_assignee: str | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    step_count: int = 0
    max_steps: int = 10  # Phase 5.4: Sufficient buffer for retries
    final_result: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    model_used: str | None = None
    task_type: str = "General"  # Phase 5.0.2: Dynamic Prompt Governance


class SupervisorDecision(BaseModel):
    next_node: Literal["marketbot", "librarian", "summary", "devbot", "david", "end", "human"] = Field(
        description="The next agent to route to, or 'end' if task is completed, or 'human' if stuck."
    )
    reasoning: str = Field(description="Why this node was selected")


# --- David's Developer Tools (Phase 5.1.3) ---
async def propose_code_fix(file_path: str, new_content: str, summary: str) -> str:
    """
    Submits a code change proposal to the Archon Server for human approval.
    Use this when you have identified a fix for a bug or a way to implement a feature.
    """
    server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
    is_docker = os.getenv("DOCKER_CONTAINER") == "true" or os.path.exists("/.dockerenv")
    server_host = "archon-server" if is_docker else "localhost"
    url = f"http://{server_host}:{server_port}/internal/david/propose"

    payload = {
        "file_path": file_path,
        "new_content": new_content,
        "summary": summary
    }

    try:
        async with httpx.AsyncClient() as client:
            # Note: In a production scenario, we'd add auth headers here.
            # For now, we rely on the internal Docker network security.
            response = await client.post(url, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            return f"✅ Proposal created successfully! ID: {data.get('id')}. Waiting for human approval."
    except Exception as e:
        logger.error(f"Failed to submit proposal: {e}")
        return f"❌ Failed to submit proposal: {str(e)}"

async def read_code_file(file_path: str) -> str:
    """
    Reads the content of a file from the codebase.
    """
    server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
    is_docker = os.getenv("DOCKER_CONTAINER") == "true" or os.path.exists("/.dockerenv")
    server_host = "archon-server" if is_docker else "localhost"
    # Reusing the existing internal proxy endpoint
    url = f"http://{server_host}:{server_port}/internal/david/read?path={file_path}"

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=5.0)
            response.raise_for_status()
            return response.text
    except Exception as e:
        return f"❌ Failed to read file: {str(e)}"


# --- Resilience Helpers (Phase 5.4.4) ---
async def _run_agent_with_retry(agent: Agent[Any, Any], prompt: str, ctx_state: SharedState, model_name: str, deps: Any = None) -> Any:
    """
    Executes an agent run with exponential backoff for 503/429 errors.
    Supports Google API Key rotation (GEMINI_API_KEY -> GOOGLE_API_KEY).
    """

    @retry_with_backoff(max_retries=5, initial_delay=2.0)
    async def _execute(override_key: str | None = None):
        if override_key:
            # Re-initialize the model with the backup key if we hit a hard quota.
            from pydantic_ai.models.gemini import GeminiModel

            # Phase 5.1.5: Version-aware Provider Selection
            if PAI_V1:
                from pydantic_ai.providers.google import GoogleProvider as ProviderClass
            else:
                from pydantic_ai.providers.google_gla import GoogleGLAProvider as ProviderClass  # type: ignore

            provider = ProviderClass(api_key=override_key)
            backup_model: Any = GeminiModel(model_name, provider=provider)  # type: ignore
            return await agent.run(prompt, model=backup_model, deps=deps)
        return await agent.run(prompt, deps=deps)
    try:
        return await _execute()
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg and ("Quota exceeded" in err_msg or "RESOURCE_EXHAUSTED" in err_msg):
            primary_key = os.getenv("GEMINI_API_KEY")
            google_key_backup = os.getenv("GOOGLE_API_KEY")

            if google_key_backup and google_key_backup != primary_key:
                logger.warning("⚠️ Primary GEMINI_API_KEY exhausted. Rotating to backup GOOGLE_API_KEY...")
                try:
                    return await _execute(override_key=google_key_backup)
                except Exception as fallback_e:
                    logger.error(f"❌ Backup GOOGLE_API_KEY also failed: {fallback_e}")
                    raise fallback_e
            else:
                logger.error(f"❌ [Hard Limit] Google API Quota exceeded and no backup rotation possible: {err_msg}")
                raise RuntimeError(f"API Daily Limit Exceeded. Details: {err_msg}") from e
        raise


def _get_output(result: Any) -> Any:
    """Compatibility helper to get result data/output across versions."""
    return getattr(result, "output", getattr(result, "data", None))


def _accumulate_usage(ctx_state: SharedState, result: Any, model_name: str):
    """Utility to safely extract and add usage tokens."""
    try:
        usage = result.usage()
        ctx_state.input_tokens += usage.request_tokens or 0
        ctx_state.output_tokens += usage.response_tokens or 0
        ctx_state.model_used = model_name
    except Exception:
        pass


# --- 2. Supervisor Node (The Brain) ---
class SupervisorNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> MarketBotNode | LibrarianNode | SummaryNode | DevBotNode | DavidNode | End[str]:
        ctx.state.step_count += 1
        logger.info(f"🕸️ [Supervisor] Step {ctx.state.step_count}/{ctx.state.max_steps}")

        if ctx.state.step_count > ctx.state.max_steps:
            logger.warning("🚫 [Supervisor] Max recursion reached. Tripping circuit breaker.")
            ctx.state.final_result = "Circuit Breaker Tripped: Needs Human Review"
            return End(ctx.state.final_result)

        model_name = os.getenv("SUPERVISOR_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] SUPERVISOR_AGENT_MODEL missing.")

        from src.server.services.prompt_service import prompt_service

        task_type = ctx.state.task_type
        if task_type == "Marketing Data Deep Dive":
            prompt_key = "WORKFLOW_SUPERVISOR_MARKETING"
        else:
            prompt_key = "WORKFLOW_SUPERVISOR_GENERAL"

        default_supervisor_prompt = (
            "You are Charlie, the Supervisor. Review the conversation history. "
            "Decide which worker should act next. "
            "- 'marketbot' writes marketing content.\n"
            "- 'librarian' searches documentation/RAG.\n"
            "- 'summary' summarizes text.\n"
            "- 'devbot' calculates statistics or writes code.\n"
            "- 'david' extracts raw data from the database.\n"
            "- 'end' if the goal is fully achieved.\n"
            "- 'human' if you are stuck or lack permissions."
        )
        system_prompt = prompt_service.get_prompt(prompt_key, default_supervisor_prompt)

        # Build agent config dynamically to avoid version mismatch errors
        agent_args: dict[str, Any] = {
            "model": model_name,
            "system_prompt": system_prompt
        }
        if PAI_V1:
            agent_args["output_type"] = SupervisorDecision
        else:
            agent_args["result_type"] = SupervisorDecision

        router_agent = Agent(**agent_args)

        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])
        try:
            result = await _run_agent_with_retry(
                router_agent, f"History:\n{history_text}\n\nDecide next step.", ctx.state, model_name
            )
            _accumulate_usage(ctx.state, result, model_name)

            decision = _get_output(result)
            logger.info(f"🧠 [Supervisor] Decision: {decision.next_node} (Reason: {decision.reasoning})")

            if decision.next_node == "end":
                ctx.state.final_result = "Workflow completed successfully."
                return End(ctx.state.final_result)
            elif decision.next_node == "human":
                ctx.state.final_result = "Escalated to human review."
                return End(ctx.state.final_result)
            elif decision.next_node == "marketbot":
                return MarketBotNode()
            elif decision.next_node == "librarian":
                return LibrarianNode()
            elif decision.next_node == "summary":
                return SummaryNode()
            elif decision.next_node == "devbot":
                return DevBotNode()
            elif decision.next_node == "david":
                return DavidNode()
            else:
                ctx.state.final_result = f"Error: Unknown decision {decision.next_node}"
                return End(ctx.state.final_result)

        except Exception as e:
            logger.error(f"Supervisor error: {e}", exc_info=True)
            ctx.state.final_result = f"Supervisor Error: {str(e)}"
            return End(ctx.state.final_result)


# --- 3. Worker Nodes (The Muscle) ---
async def _run_generic_worker(
    ctx: GraphRunContext[SharedState],
    role_name: str,
    prompt_key: str,
    default_prompt: str,
    task_instruction: str,
) -> SupervisorNode:
    logger.info(f"🛠️ [{role_name}] Executing task...")
    model_name = os.getenv("WORKER_AGENT_MODEL")
    if not model_name:
        raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL missing.")

    from src.server.services.prompt_service import prompt_service
    system_prompt = prompt_service.get_prompt(prompt_key, default_prompt)
    agent = Agent(model=model_name, system_prompt=system_prompt)
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

    try:
        res = await _run_agent_with_retry(
            agent, f"{task_instruction}\n{history_text}", ctx.state, model_name
        )
        _accumulate_usage(ctx.state, res, model_name)
        ctx.state.messages.append({"role": role_name.lower(), "content": str(_get_output(res))})
    except Exception as e:
        logger.error(f"{role_name} error: {e}")
        ctx.state.messages.append({"role": role_name.lower(), "content": f"Error: {e}"})

    return SupervisorNode()


class MarketBotNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        task_type = ctx.state.task_type
        prompt_key = "WORKFLOW_STRATEGIST_BOB" if task_type == "Marketing Data Deep Dive" else "WORKFLOW_WORKER_MARKETBOT"
        return await _run_generic_worker(
            ctx, "MarketBot", prompt_key, "You are a marketing copywriter. Be concise.", "Based on history, provide the marketing copy."
        )


class LibrarianNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [Librarian] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL not found for LibrarianNode.")

        from src.agents.rag_agent import RagAgent, RagDependencies

        # Instantiate RagAgent which already has RAG tools registered
        rag_agent_wrapper = RagAgent(model=model_name)
        # Get the underlying PydanticAI agent to use with our retry helper
        agent = rag_agent_wrapper._agent

        # Setup dependencies for RAG tools
        deps = RagDependencies(match_count=3)

        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            # Phase 5.1.4: Hunter Mode - Librarian can now crawl external sites if internal search is insufficient
            instruction = (
                "Extract facts from history by searching available knowledge.\n"
                "If the internal knowledge base does not contain the required information, "
                "or if the user provides a specific URL, use the web_crawl_tool to get the latest data."
            )
            res = await _run_agent_with_retry(
                agent, f"{instruction}\n{history_text}", ctx.state, model_name, deps=deps
            )
            _accumulate_usage(ctx.state, res, model_name)

            # Phase 5.1.4: Citation Transparency - Pass collected citations to state
            ctx.state.messages.append({
                "role": "librarian",
                "content": str(res.output),
                "citations": deps.collected_citations
            })
        except Exception as e:
            logger.error(f"Librarian error: {e}")
            ctx.state.messages.append({"role": "librarian", "content": f"Error: {e}"})

        return SupervisorNode()


class SummaryNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        return await _run_generic_worker(
            ctx, "Summary", "WORKFLOW_WORKER_SUMMARY", "You summarize text into bullet points.", "Summarize the conversation:"
        )


class DevBotNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        return await _run_generic_worker(
            ctx, "DevBot", "WORKFLOW_SCIENTIST_DEVBOT", "You are DevBot, a data scientist.", "Task from Supervisor:"
        )


class DavidNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [David] Thinking about code changes...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL missing.")

        from src.server.services.prompt_service import prompt_service
        system_prompt = prompt_service.get_prompt(
            "WORKFLOW_DATA_DAVID",
            "You are David, the Senior Developer. You can read code and propose fixes using tools."
        )

        agent = Agent(
            model=model_name,
            system_prompt=system_prompt,
            tools=[propose_code_fix, read_code_file]
        )

        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await _run_agent_with_retry(
                agent,
                f"Review the history and use tools if needed to fix code or extract data.\n{history_text}",
                ctx.state,
                model_name
            )
            _accumulate_usage(ctx.state, res, model_name)
            ctx.state.messages.append({"role": "david", "content": str(_get_output(res))})
        except Exception as e:
            logger.error(f"David error: {e}")
            ctx.state.messages.append({"role": "david", "content": f"Error: {e}"})

        return SupervisorNode()


# --- 4. The Graph Orchestrator ---
workflow_graph = Graph(nodes=[SupervisorNode, MarketBotNode, LibrarianNode, SummaryNode, DevBotNode, DavidNode])


class WorkflowEngine:
    """Wrapper to run the graph and manage the state."""

    async def run_workflow(self, initial_prompt: str, task_type: str = "General") -> dict[str, Any]:
        state = SharedState(
            messages=[{"role": "user", "content": initial_prompt}],
            task_type=task_type
        )
        try:
            run_result = await workflow_graph.run(SupervisorNode(), state=state)
            final_state = run_result.state

            # Phase 5.4: Fix Token Logging Gap
            try:
                if final_state.input_tokens > 0 or final_state.output_tokens > 0:
                    server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
                    async with httpx.AsyncClient() as client:
                        payload = {
                            "model": final_state.model_used or "workflow-engine",
                            "provider": "google",
                            "input_tokens": final_state.input_tokens,
                            "output_tokens": final_state.output_tokens,
                            "context_type": "agentic_workflow",
                        }
                        is_docker = os.getenv("DOCKER_CONTAINER") == "true" or os.path.exists("/.dockerenv")
                        server_host = "archon-server" if is_docker else "localhost"
                        await client.post(
                            f"http://{server_host}:{server_port}/internal/stats/token-usage",
                            json=payload,
                            timeout=5.0,
                        )
                        logger.info("📊 Token usage logged via Internal API")
            except Exception as e:
                logger.warning(f"⚠️ Failed to log token usage: {e}")

            final_res_str = ""
            if final_state.final_result and "Workflow completed successfully" in final_state.final_result:
                # Extract the last message from a worker as the result
                for msg in reversed(final_state.messages):
                    if msg.get("role") in ["marketbot", "librarian", "summary", "devbot", "david"]:
                        final_res_str = msg.get("content", "")
                        break

            if not final_res_str:
                final_res_str = str(final_state.final_result or _get_output(run_result))

            is_success = "Supervisor Error:" not in final_res_str and "Circuit Breaker Tripped:" not in final_res_str

            return {
                "success": is_success,
                "final_result": final_res_str,
                "step_count": final_state.step_count,
                "messages": final_state.messages,
            }
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "step_count": state.step_count,
                "messages": state.messages,
            }
