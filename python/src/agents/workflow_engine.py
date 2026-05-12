from __future__ import annotations

import logging
import os
from typing import Any, Literal

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_graph import BaseNode, End, Graph, GraphRunContext

logger = logging.getLogger(__name__)

# --- 1. Shared State ---
class SharedState(BaseModel):
    messages: list[dict[str, str]] = Field(default_factory=list)
    current_assignee: str | None = None
    artifacts: dict[str, Any] = Field(default_factory=dict)
    step_count: int = 0
    max_steps: int = 3
    final_result: str | None = None

class SupervisorDecision(BaseModel):
    next_node: Literal["marketbot", "librarian", "summary", "end", "human"] = Field(
        description="The next agent to route to, or 'end' if task is completed, or 'human' if stuck."
    )
    reasoning: str = Field(description="Why this node was selected")

# --- 2. Supervisor Node (The Brain) ---
class SupervisorNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> MarketBotNode | LibrarianNode | SummaryNode | End[str]:
        ctx.state.step_count += 1
        logger.info(f"🕸️ [Supervisor] Step {ctx.state.step_count}/{ctx.state.max_steps}")

        if ctx.state.step_count > ctx.state.max_steps:
            logger.warning("🚫 [Supervisor] Max recursion reached. Tripping circuit breaker.")
            ctx.state.final_result = "Circuit Breaker Tripped: Needs Human Review"
            return End(ctx.state.final_result)

        model_name = os.getenv("SUPERVISOR_AGENT_MODEL", "gemini-3-flash-preview")

        router_agent = Agent(
            model=model_name,
            result_type=SupervisorDecision,
            system_prompt=(
                "You are Charlie, the Supervisor. Review the conversation history. "
                "Decide which worker should act next. "
                "- 'marketbot' writes marketing content.\n"
                "- 'librarian' searches documentation/RAG.\n"
                "- 'summary' summarizes text.\n"
                "- 'end' if the goal is fully achieved.\n"
                "- 'human' if you are stuck or lack permissions."
            )
        )

        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])
        try:
            result = await router_agent.run(f"History:\n{history_text}\n\nDecide next step.")
            decision: SupervisorDecision = result.data
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
            logger.error(f"Supervisor error: {e}")
            return End(f"Supervisor Error: {str(e)}")

# --- 3. Worker Nodes (The Muscle) ---
class MarketBotNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [MarketBot] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL", "gemini-3.1-flash-lite-preview")

        agent = Agent(model=model_name, system_prompt="You are a marketing copywriter. Be concise.")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await agent.run(f"Based on history, provide the marketing copy.\n{history_text}")
            ctx.state.messages.append({"role": "marketbot", "content": res.data})
        except Exception as e:
            ctx.state.messages.append({"role": "marketbot", "content": f"Error: {e}"})

        return SupervisorNode()

class LibrarianNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [Librarian] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL", "gemini-3.1-flash-lite-preview")

        agent = Agent(model=model_name, system_prompt="You are a researcher. Summarize facts.")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await agent.run(f"Extract facts from history.\n{history_text}")
            ctx.state.messages.append({"role": "librarian", "content": res.data})
        except Exception as e:
            ctx.state.messages.append({"role": "librarian", "content": f"Error: {e}"})

        return SupervisorNode()

class SummaryNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [SummaryAgent] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL", "gemini-3.1-flash-lite-preview")

        agent = Agent(model=model_name, system_prompt="You summarize text into bullet points.")
        history_text = "\n".join([f"{m['role']}: {m['content']}" for m in ctx.state.messages])

        try:
            res = await agent.run(f"Summarize the conversation:\n{history_text}")
            ctx.state.messages.append({"role": "summary", "content": res.data})
        except Exception as e:
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
            return {
                "success": True,
                "final_result": final_state.final_result or run_result.output,
                "step_count": final_state.step_count,
                "messages": final_state.messages
            }
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "step_count": state.step_count,
                "messages": state.messages
            }
