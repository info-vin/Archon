from __future__ import annotations

import logging
import os
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

from src.server.utils.retry_utils import retry_with_backoff

logger = logging.getLogger(__name__)


# --- 1. Shared State ---
class SharedState(BaseModel):
    messages: list[dict[str, str]] = Field(default_factory=list)
    current_assignee: str | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    step_count: int = 0
    max_steps: int = 10  # Phase 5.4: Increased to allow retries and longer workflows
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
    Inherits proven defense patterns from src.server.utils.retry_utils.
    """

    @retry_with_backoff(max_retries=5, initial_delay=2.0)
    async def _execute():
        return await agent.run(prompt)

    try:
        result = await _execute()
        # Accumulate usage
        usage = result.usage()
        ctx_state.input_tokens += usage.request_tokens or 0
        ctx_state.output_tokens += usage.response_tokens or 0
        ctx_state.model_used = model_name
        return result
    except Exception as e:
        err_msg = str(e)
        if "Quota exceeded" in err_msg and "Free Tier" in err_msg:
            # Special handling for hard daily limits
            logger.error(f"❌ [Hard Limit] Gemini Free Tier RPD exceeded: {err_msg}")
            raise RuntimeError(
                f"API Daily Limit Exceeded. Please try again tomorrow or use a Paid Tier key. Details: {err_msg}"
            ) from e
        raise


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
            raise ValueError("❌ [SSOT Violation] SUPERVISOR_AGENT_MODEL not found in environment or credentials.")

        # Container uses PydanticAI 1.44.0, which uses 'output_type'
        # Local linter (0.0.55) fails this, so we ignore.
        router_agent = Agent(
            model=model_name,
            output_type=SupervisorDecision,  # type: ignore
            system_prompt=(
                "You are Charlie, the Supervisor. Review the conversation history. "
                "Decide which worker should act next. "
                "- 'marketbot' writes marketing content.\n"
                "- 'librarian' searches documentation/RAG.\n"
                "- 'summary' summarizes text.\n"
                "- 'end' if the goal is fully achieved.\n"
                "- 'human' if you are stuck or lack permissions."
            ),
        )

        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])
        try:
            # Use the new resilient runner
            result = await _run_agent_with_retry(
                router_agent, f"History:\n{history_text}\n\nDecide next step.", ctx.state, model_name
            )

            # Container uses PydanticAI 1.44.0, which uses result.output
            # Local linter (0.0.55) fails this, so we ignore.
            decision: SupervisorDecision = result.output
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
                return End("Error: Unknown routing decision.")

        except Exception as e:
            logger.error(f"Supervisor error: {e}", exc_info=True)
            return End(f"Supervisor Error: {str(e)}")


# --- 3. Worker Nodes (The Muscle) ---
class MarketBotNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [MarketBot] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL not found for MarketBotNode.")

        agent = Agent(model=model_name, system_prompt="You are a marketing copywriter. Be concise.")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await _run_agent_with_retry(
                agent, f"Based on history, provide the marketing copy.\n{history_text}", ctx.state, model_name
            )
            # Container uses PydanticAI 1.44.0, which uses res.output
            ctx.state.messages.append({"role": "marketbot", "content": str(res.output)})  # type: ignore
        except Exception as e:
            logger.error(f"MarketBot error: {e}")
            ctx.state.messages.append({"role": "marketbot", "content": f"Error: {e}"})

        return SupervisorNode()


class LibrarianNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [Librarian] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL not found for LibrarianNode.")

        agent = Agent(model=model_name, system_prompt="You are a researcher. Summarize facts.")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await _run_agent_with_retry(
                agent, f"Extract facts from history.\n{history_text}", ctx.state, model_name
            )
            # Container uses PydanticAI 1.44.0, which uses res.output
            ctx.state.messages.append({"role": "librarian", "content": str(res.output)})  # type: ignore
        except Exception as e:
            logger.error(f"Librarian error: {e}")
            ctx.state.messages.append({"role": "librarian", "content": f"Error: {e}"})

        return SupervisorNode()


class SummaryNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [SummaryAgent] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL not found for SummaryNode.")

        agent = Agent(model=model_name, system_prompt="You summarize text into bullet points.")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await _run_agent_with_retry(
                agent, f"Summarize the conversation:\n{history_text}", ctx.state, model_name
            )
            # Container uses PydanticAI 1.44.0, which uses res.output
            ctx.state.messages.append({"role": "summary", "content": str(res.output)})
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
                        # Use archon-server when in docker
                        is_docker = os.getenv("DOCKER_CONTAINER") == "true" or os.path.exists("/.dockerenv")
                        server_host = "archon-server" if is_docker else "localhost"
                        await client.post(
                            f"http://{server_host}:{server_port}/internal/stats/token-usage",
                            json=payload,
                            timeout=5.0,
                        )
                        logger.info(
                            f"📊 Token usage logged: {final_state.input_tokens} input, {final_state.output_tokens} output"
                        )
            except Exception as e:
                logger.warning(f"⚠️ Failed to log token usage: {e}")

            return {
                "success": True,
                "final_result": final_state.final_result or run_result.output,  # type: ignore
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
