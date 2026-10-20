from __future__ import annotations

import logging
import os
from typing import Any

from pydantic_ai import Agent
from pydantic_graph import BaseNode, End, GraphRunContext

from src.server.services.shared_constants import PromptNameEnum, TaskFeatureEnum

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
            from src.server.config.model_ssot import SYSTEM_MODELS

            model_name = SYSTEM_MODELS["DEFAULT_PRO"].replace("models/", "")

        from src.server.services.prompt_service import prompt_service
        from src.server.utils import get_supabase_client

        task_type = ctx.state.task_type

        # 1. Try to load routing and prompt configuration from database dynamically
        prompt_key = PromptNameEnum.WORKFLOW_SUPERVISOR_GENERAL
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
            query = supabase.table("archon_workflow_flows").select("*")
            success, res = repo.execute_query(query, "Failed to load workflow config")

            if success and res.get("data"):
                # Normalized matching ignoring case, spaces, and underscores
                target_key = (task_type or "").lower().replace(" ", "").replace("_", "")
                matched_flow = None
                for flow in res["data"]:
                    wf_type = str(flow.get("workflow_type", "")).lower().replace(" ", "").replace("_", "")
                    if wf_type == target_key:
                        matched_flow = flow
                        break

                if matched_flow:
                    prompt_key = matched_flow.get("supervisor_prompt_name", prompt_key)
                    db_routing = matched_flow.get("node_routing")
                    if isinstance(db_routing, dict):
                        node_routing.update(db_routing)
        except Exception as e:
            logger.warning(f"Failed to load dynamic workflow config from DB: {e}")

        default_supervisor_prompt = "You are Charlie, the Supervisor. Please answer." # Kept minimal as SSOT is the source

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

            # Anti-recursion safeguard: prevent routing back-to-back to the exact same worker in Daily Summary
            is_daily = (ctx.state.task_type or "").lower().replace(" ", "").replace("_", "") == "dailyexecutivesummary"
            if is_daily:
                if (
                    ctx.state.messages
                    and next_step in ["marketbot", "devbot", "summary", "librarian", "david", "bob"]
                    and ctx.state.messages[-1].get("role") in [next_step, "MarketBot", "DevBot", "Summary", "Bob"]
                ):
                    logger.warning(
                        f"⚠️ [Supervisor] Detected consecutive routing to '{next_step}' in Daily Summary. Auto-advancing workflow..."
                    )
                    if next_step in ["marketbot", "bob"]:
                        next_step = "devbot"
                    elif next_step == "devbot":
                        next_step = "summary"
                    elif next_step == "summary":
                        ctx.state.final_result = "Workflow completed successfully."
                        return End(ctx.state.final_result)

            if next_step == "end":
                ctx.state.final_result = "Workflow completed successfully."
                return End(ctx.state.final_result)
            elif next_step == "human":
                ctx.state.final_result = "Escalated to human review."
                return End(ctx.state.final_result)

            # Node alias normalization (e.g. "bob" or "MarketBot" -> "marketbot")
            if next_step in ["bob", "MarketBot"]:
                next_step = "marketbot"
            elif next_step in ["DevBot"]:
                next_step = "devbot"
            elif next_step in ["Summary"]:
                next_step = "summary"
            elif next_step in ["Librarian"]:
                next_step = "librarian"
            elif next_step in ["David"]:
                next_step = "david"

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
        from src.server.config.model_ssot import SYSTEM_MODELS

        model_name = SYSTEM_MODELS["DEFAULT_TEXT"].replace("models/", "")

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
            PromptNameEnum.WORKFLOW_STRATEGIST_BOB if task_type == TaskFeatureEnum.MARKETING_DATA_DEEP_DIVE else PromptNameEnum.WORKFLOW_WORKER_MARKETBOT
        )
        is_daily = (task_type or "").lower().replace(" ", "").replace("_", "") == "dailyexecutivesummary"
        task_instruction = (
            "請針對對話歷史中提供的昨日 sales 與 leads 轉換指標進行商業評估與簡短分析。"
            if is_daily
            else "Based on history, provide the marketing copy."
        )
        return await _run_generic_worker(
            ctx,
            "MarketBot",
            prompt_key,
            "You are a marketing copywriter. Be concise.",
            task_instruction,
        )


class LibrarianNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [Librarian] Executing task...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            from src.server.config.model_ssot import SYSTEM_MODELS

            model_name = SYSTEM_MODELS["DEFAULT_TEXT"].replace("models/", "")

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
        task_type = ctx.state.task_type
        is_daily = (task_type or "").lower().replace(" ", "").replace("_", "") == "dailyexecutivesummary"
        task_instruction = (
            "請將團隊討論與指標數據，彙整為具備 Markdown 表格與比率公式定義的專業每日執行摘要："
            if is_daily
            else "Summarize the conversation and metrics into the requested structured report format:"
        )
        return await _run_generic_worker(
            ctx,
            "Summary",
            PromptNameEnum.WORKFLOW_WORKER_SUMMARY,
            "You summarize the team discussion into a professional Executive Summary with structured Markdown tables and metric definitions.",
            task_instruction,
        )


class DevBotNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        task_type = ctx.state.task_type
        is_daily = (task_type or "").lower().replace(" ", "").replace("_", "") == "dailyexecutivesummary"
        task_instruction = (
            "請針對對話歷史中昨日的系統健康狀態、API 警告、token 消耗及估計成本進行技術分析。"
            if is_daily
            else "Task from Supervisor:"
        )
        await _run_generic_worker(
            ctx, "DevBot", PromptNameEnum.WORKFLOW_SCIENTIST_DEVBOT, "You are DevBot, a data scientist.", task_instruction
        )
        return SupervisorNode()


class DavidNode(BaseNode[SharedState, None, str]):
    async def run(self, ctx: GraphRunContext[SharedState]) -> SupervisorNode:
        logger.info("🛠️ [David] Thinking about code changes...")
        model_name = os.getenv("WORKER_AGENT_MODEL")
        if not model_name:
            from src.server.config.model_ssot import SYSTEM_MODELS

            model_name = SYSTEM_MODELS["DEFAULT_TEXT"].replace("models/", "")

        from src.server.services.prompt_service import prompt_service

        system_prompt = prompt_service.get_prompt(
            PromptNameEnum.WORKFLOW_DATA_DAVID,
            "You are David, the Senior Developer.",
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
