from __future__ import annotations

import logging
import os
from typing import Any

from pydantic_ai import Agent
from pydantic_graph import BaseNode, End, GraphRunContext

from .state import SharedState, SupervisorDecision
from .tools import propose_code_fix, read_code_file
from .utils import PAI_V1, _accumulate_usage, _build_pruned_history, _get_output, _run_agent_with_retry

logger = logging.getLogger(__name__)


# --- 2. Supervisor Node (The Brain) ---
class SupervisorNode(BaseNode[SharedState, None, str]):
    async def run(
        self, ctx: GraphRunContext[SharedState]
    ) -> MarketBotNode | LibrarianNode | SummaryNode | DevBotNode | DavidNode | End[str]:
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
        from src.server.utils import get_supabase_client

        task_type = ctx.state.task_type

        # 1. Try to load routing and prompt configuration from database dynamically
        prompt_key = "WORKFLOW_SUPERVISOR_GENERAL"
        node_routing = {
            "marketbot": "MarketBotNode",
            "librarian": "LibrarianNode",
            "summary": "SummaryNode",
            "devbot": "DevBotNode",
            "david": "DavidNode"
        }

        try:
            from src.server.repositories.base_repository import BaseRepository

            supabase = get_supabase_client()
            repo = BaseRepository(supabase)
            query = supabase.table("archon_workflow_flows").select("*").eq("workflow_type", task_type)
            success, res = repo.execute_query(query, "Failed to load workflow config")

            if success and res.get("data"):
                flow_data = res["data"][0]
                prompt_key = flow_data["supervisor_prompt_name"]
                node_routing = flow_data["node_routing"]
        except Exception:
            pass

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
        agent_args: dict[str, Any] = {"model": model_name, "system_prompt": system_prompt}
        if PAI_V1:
            agent_args["output_type"] = SupervisorDecision
        else:
            agent_args["result_type"] = SupervisorDecision

        router_agent = Agent(**agent_args)

        history_text = _build_pruned_history(ctx.state.messages)
        try:
            result = await _run_agent_with_retry(
                router_agent, f"History:\n{history_text}\n\nDecide next step.", ctx.state, model_name
            )
            _accumulate_usage(ctx.state, result, model_name)

            decision = _get_output(result)
            logger.info(f"🧠 [Supervisor] Decision: {decision.next_node} (Reason: {decision.reasoning})")

            next_step = decision.next_node

            if next_step == "end":
                ctx.state.final_result = "Workflow completed successfully."
                return End(ctx.state.final_result)
            elif next_step == "human":
                ctx.state.final_result = "Escalated to human review."
                return End(ctx.state.final_result)

            # Map the next node routing name from database to static Class Node return signatures
            target_node_name = node_routing.get(next_step)
            if target_node_name == "MarketBotNode":
                return MarketBotNode()
            elif target_node_name == "LibrarianNode":
                return LibrarianNode()
            elif target_node_name == "SummaryNode":
                return SummaryNode()
            elif target_node_name == "DevBotNode":
                return DevBotNode()
            elif target_node_name == "DavidNode":
                return DavidNode()
            else:
                ctx.state.final_result = f"Error: Unknown decision {next_step} or unmapped node {target_node_name}"
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
    history_text = _build_pruned_history(ctx.state.messages)

    try:
        res = await _run_agent_with_retry(agent, f"{task_instruction}\n{history_text}", ctx.state, model_name)
        _accumulate_usage(ctx.state, res, model_name)
        ctx.state.messages.append({"role": role_name.lower(), "content": str(_get_output(res))})
    except Exception as e:
        logger.error(f"{role_name} error: {e}")
        ctx.state.messages.append({"role": role_name.lower(), "content": f"Error: {e}"})

    return SupervisorNode()


class MarketBotNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        task_type = ctx.state.task_type
        prompt_key = (
            "WORKFLOW_STRATEGIST_BOB" if task_type == "Marketing Data Deep Dive" else "WORKFLOW_WORKER_MARKETBOT"
        )
        return await _run_generic_worker(
            ctx,
            "MarketBot",
            prompt_key,
            "You are a marketing copywriter. Be concise. You MUST write your response in Traditional Chinese (繁體中文).",
            "Based on history, provide the marketing copy.",
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

        history_text = _build_pruned_history(ctx.state.messages)

        try:
            # Phase 5.1.4: Hunter Mode - Librarian can now crawl external sites if internal search is insufficient
            instruction = (
                "Extract facts from history by searching available knowledge.\n"
                "If the internal knowledge base does not contain the required information, "
                "or if the user provides a specific URL, use the web_crawl_tool to get the latest data."
            )
            res = await _run_agent_with_retry(agent, f"{instruction}\n{history_text}", ctx.state, model_name, deps=deps)
            _accumulate_usage(ctx.state, res, model_name)

            # Phase 5.1.4: Citation Transparency - Pass collected citations to state
            ctx.state.messages.append(
                {"role": "librarian", "content": str(_get_output(res)), "citations": deps.collected_citations}
            )
        except Exception as e:
            logger.error(f"Librarian error: {e}")
            ctx.state.messages.append({"role": "librarian", "content": f"Error: {e}"})

        return SupervisorNode()


class SummaryNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        return await _run_generic_worker(
            ctx,
            "Summary",
            "WORKFLOW_WORKER_SUMMARY",
            "You summarize text into bullet points. You MUST write your response in Traditional Chinese (繁體中文).",
            "Summarize the conversation:",
        )


class DevBotNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        await _run_generic_worker(
            ctx, "DevBot", "WORKFLOW_SCIENTIST_DEVBOT", "You are DevBot, a data scientist. You MUST write your response in Traditional Chinese (繁體中文).", "Task from Supervisor:"
        )
        return SupervisorNode()


class DavidNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [David] Thinking about code changes...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            raise ValueError("❌ [SSOT Violation] WORKER_AGENT_MODEL missing.")

        from src.server.services.prompt_service import prompt_service

        system_prompt = prompt_service.get_prompt(
            "WORKFLOW_DATA_DAVID",
            "You are David, the Senior Developer. You can read code and propose fixes using tools. You MUST write your response in Traditional Chinese (繁體中文).",
        )

        agent = Agent(model=model_name, system_prompt=system_prompt, tools=[propose_code_fix, read_code_file])

        history_text = _build_pruned_history(ctx.state.messages)

        try:
            res = await _run_agent_with_retry(
                agent,
                f"Review the history and use tools if needed to fix code or extract data.\n{history_text}",
                ctx.state,
                model_name,
            )
            _accumulate_usage(ctx.state, res, model_name)
            ctx.state.messages.append({"role": "david", "content": str(_get_output(res))})
        except Exception as e:
            logger.error(f"David error: {e}")
            ctx.state.messages.append({"role": "david", "content": f"Error: {e}"})

        return SupervisorNode()
