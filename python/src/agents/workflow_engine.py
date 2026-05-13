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
    messages: list[dict[str, str]] = Field(default_factory=list)
    current_assignee: str | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    step_count: int = 0
    max_steps: int = 10  # Phase 5.4: Sufficient buffer for retries
    final_result: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    model_used: str | None = None


class SupervisorDecision(BaseModel):
    next_node: Literal["marketbot", "librarian", "summary", "end", "human"] = Field(
        description="The next agent to route to, or 'end' if task is completed, or 'human' if stuck."
    )
    reasoning: str = Field(description="Why this node was selected")


# --- Resilience Helpers (Phase 5.4.4) ---
async def _run_agent_with_retry(agent: Agent[Any, Any], prompt: str, ctx_state: SharedState, model_name: str) -> Any:
    """
    Executes an agent run with exponential backoff for 503/429 errors.
    Supports Google API Key rotation (GEMINI_API_KEY -> GOOGLE_API_KEY).
    """

    @retry_with_backoff(max_retries=5, initial_delay=2.0)
    async def _execute(override_key: str | None = None):
        if override_key:
            from pydantic_ai.models.gemini import GeminiModel
            from pydantic_ai.providers.google_gla import GoogleGLAProvider

            provider = GoogleGLAProvider(api_key=override_key)
            backup_model: Any = GeminiModel(model_name, provider=provider)
            return await agent.run(prompt, model=backup_model)
        return await agent.run(prompt)

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
    async def run(self, ctx: GraphRunContext[SharedState]) -> MarketBotNode | LibrarianNode | SummaryNode | End[str]:
        ctx.state.step_count += 1
        logger.info(f"🕸️ [Supervisor] Step {ctx.state.step_count}/{ctx.state.max_steps}")

        if ctx.state.step_count > ctx.state.max_steps:
            logger.warning("🚫 [Supervisor] Max recursion reached. Tripping circuit breaker.")
            ctx.state.final_result = "Circuit Breaker Tripped: Needs Human Review"
            return End(ctx.state.final_result)

        model_name = os.getenv("SUPERVISOR_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] SUPERVISOR_AGENT_MODEL missing.")

        # Build agent config dynamically to avoid version mismatch errors
        agent_args: dict[str, Any] = {
            "model": model_name,
            "system_prompt": (
                "You are Charlie, the Supervisor. Review the conversation history. "
                "Decide which worker should act next. "
                "- 'marketbot' writes marketing content.\n"
                "- 'librarian' searches documentation/RAG.\n"
                "- 'summary' summarizes text.\n"
                "- 'end' if the goal is fully achieved.\n"
                "- 'human' if you are stuck or lack permissions."
            )
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
            else:
                ctx.state.final_result = f"Error: Unknown decision {decision.next_node}"
                return End(ctx.state.final_result)

        except Exception as e:
            logger.error(f"Supervisor error: {e}", exc_info=True)
            ctx.state.final_result = f"Supervisor Error: {str(e)}"
            return End(ctx.state.final_result)


# --- 3. Worker Nodes (The Muscle) ---
class MarketBotNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [MarketBot] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL missing.")

        agent = Agent(model=model_name, system_prompt="You are a marketing copywriter. Be concise.")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await _run_agent_with_retry(
                agent, f"Based on history, provide the marketing copy.\n{history_text}", ctx.state, model_name
            )
            _accumulate_usage(ctx.state, res, model_name)
            ctx.state.messages.append({"role": "marketbot", "content": str(_get_output(res))})
        except Exception as e:
            logger.error(f"MarketBot error: {e}")
            ctx.state.messages.append({"role": "marketbot", "content": f"Error: {e}"})

        return SupervisorNode()


class LibrarianNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [Librarian] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL missing.")

        agent = Agent(model=model_name, system_prompt="You are a researcher. Summarize facts.")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await _run_agent_with_retry(
                agent, f"Extract facts from history.\n{history_text}", ctx.state, model_name
            )
            _accumulate_usage(ctx.state, res, model_name)
            ctx.state.messages.append({"role": "librarian", "content": str(_get_output(res))})
        except Exception as e:
            logger.error(f"Librarian error: {e}")
            ctx.state.messages.append({"role": "librarian", "content": f"Error: {e}"})

        return SupervisorNode()


class SummaryNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [SummaryAgent] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL missing.")

        agent = Agent(model=model_name, system_prompt="You summarize text into bullet points.")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await _run_agent_with_retry(
                agent, f"Summarize the conversation:\n{history_text}", ctx.state, model_name
            )
            _accumulate_usage(ctx.state, res, model_name)
            ctx.state.messages.append({"role": "summary", "content": str(_get_output(res))})
        except Exception as e:
            logger.error(f"SummaryAgent error: {e}")
            ctx.state.messages.append({"role": "summary", "content": f"Error: {e}"})

        return SupervisorNode()


# --- 4. The Graph Orchestrator ---
workflow_graph = Graph(nodes=[SupervisorNode, MarketBotNode, LibrarianNode, SummaryNode])


class WorkflowEngine:
    """Wrapper to run the graph and manage the state."""

    async def run_workflow(self, initial_prompt: str) -> dict[str, Any]:
        state = SharedState(messages=[{"role": "user", "content": initial_prompt}])
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
                    if msg.get("role") in ["marketbot", "librarian", "summary"]:
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
