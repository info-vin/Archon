"""
Experimental GraphBuilder Implementation (Phase 5.1.10 / Fan-out)
This module explores the pydantic_graph.beta.GraphBuilder API for parallel execution (Fan-out)
and map-reduce patterns. It is kept isolated from the production `engine.py` to prevent regressions.
"""

import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import Any

from pydantic_ai import Agent
from pydantic_graph.beta import GraphBuilder

from src.agents.workflow.state import SharedState
from src.agents.workflow.utils import _accumulate_usage, _build_pruned_history, _run_agent_with_retry
from src.server.services.prompt_service import prompt_service
from src.server.services.shared_constants import PromptNameEnum

logger = logging.getLogger(__name__)


# --- Experimental Beta State ---
@dataclass
class BetaState:
    shared: SharedState = field(default_factory=SharedState)
    map_results: dict[str, str] = field(default_factory=dict)


# Our graph dependencies will be the standard DepsT (e.g. any context we need)
builder = GraphBuilder(state_type=BetaState, deps_type=Any, output_type=str)

# 3. Inject Semaphore: asyncio.Semaphore(2) for Free-Tier 429 protection
sem = asyncio.Semaphore(2)

# --- Define Specialized Agents ---
# Fetch model from environment or fallback, instead of hardcoding
MODEL = os.getenv("WORKER_AGENT_MODEL", "gemini-3.1-flash-lite")

@builder.step
async def supervisor_step(ctx: Any) -> list[str]:
    """
    Supervisor returning a list of targets to map over.
    This triggers the Map phase.
    """
    logger.info("🧪 [Beta Graph] Supervisor thinking... Dispatching to workers.")
    return ["sales", "marketing", "system"]


@builder.step
async def worker_step(ctx: Any) -> dict[str, str]:
    """
    Worker node for Fan-out. Processes individual targets concurrently using physical LLMs.
    """
    target = ctx.inputs

    async with sem:
        logger.info(f"👷 [Worker] Processing target: {target} (Semaphore Acquired)")

        # Determine the agent and fetch dynamic prompt
        if target == "sales":
            prompt_text = prompt_service.get_prompt(PromptNameEnum.MAP_REDUCE_ALICE_PROMPT, "You are Alice.")
            agent = Agent(model=MODEL, system_prompt=prompt_text)
        elif target == "marketing":
            prompt_text = prompt_service.get_prompt(PromptNameEnum.MAP_REDUCE_BOB_PROMPT, "You are Bob.")
            agent = Agent(model=MODEL, system_prompt=prompt_text)
        elif target == "system":
            prompt_text = prompt_service.get_prompt(PromptNameEnum.MAP_REDUCE_SYSTEM_PROMPT, "You are System Monitor.")
            agent = Agent(model=MODEL, system_prompt=prompt_text)
        else:
            return {target: f"Unknown target '{target}'."}

        # Build prompt using the shared history
        context = (
            _build_pruned_history(ctx.state.shared.messages)
            if ctx.state.shared.messages
            else "Please provide a general insight."
        )
        prompt = f"Target area: {target.upper()}\nContext:\n{context}\n\nPlease generate your insight."

        try:
            # Enforce the use of _run_agent_with_retry for ROI tracking & 429 protection
            res = await _run_agent_with_retry(
                agent, prompt, ctx_state=ctx.state.shared, model_name=MODEL, deps=ctx.deps
            )
            output = res.data if hasattr(res, "data") else res.output if hasattr(res, "output") else str(res)
            _accumulate_usage(ctx.state.shared, res, MODEL)
            logger.info(f"👷 [Worker] Completed target: {target}")
            return {target: output}
        except Exception as e:
            logger.error(f"❌ [Worker] Failed processing {target}: {e}")
            return {target: f"Failed due to error: {str(e)}"}


def reduce_results(current: dict[str, str], incoming: dict[str, str]) -> dict[str, str]:
    """Reducer function for the Join node (Reduce phase)"""
    current.update(incoming)
    return current


# Create the Join node
join_node = builder.join(reduce_results, initial_factory=dict)


@builder.step
async def final_summary_step(ctx: Any) -> str:
    """
    Final node that aggregates the mapped results into a summary via LLM.
    """
    logger.info("📊 [Beta Graph] Generating Final Summary from Map-Reduce (LLM Call)...")

    # Store aggregated results in state
    ctx.state.map_results = ctx.inputs

    # Format the inputs for the supervisor
    combined_reports = "Here are the reports from the sub-agents:\n"
    for k, v in ctx.inputs.items():
        combined_reports += f"--- {k.upper()} REPORT ---\n{v}\n\n"

    # Get supervisor agent with dynamic prompt
    prompt_text = prompt_service.get_prompt(PromptNameEnum.MAP_REDUCE_SUPERVISOR_PROMPT, "You are Supervisor.")
    supervisor_agent = Agent(model=MODEL, system_prompt=prompt_text)

    try:
        res = await _run_agent_with_retry(
            supervisor_agent, combined_reports, ctx_state=ctx.state.shared, model_name=MODEL, deps=ctx.deps
        )
        output = res.data if hasattr(res, "data") else res.output if hasattr(res, "output") else str(res)
        _accumulate_usage(ctx.state.shared, res, MODEL)
        ctx.state.shared.final_result = output
        logger.info("✅ [Beta Graph] Final Output Generated.")
        return output
    except Exception as e:
        logger.error(f"❌ [Beta Graph] Supervisor failed: {e}")
        return f"Failed to generate summary: {str(e)}"


# Wire up the edges for fan-out
builder.add_edge(source=builder.start_node, destination=supervisor_step)
builder.add_mapping_edge(source=supervisor_step, map_to=worker_step)
builder.add_edge(source=worker_step, destination=join_node)
builder.add_edge(source=join_node, destination=final_summary_step)
builder.add_edge(source=final_summary_step, destination=builder.end_node)

beta_graph = builder.build()

if __name__ == "__main__":
    # Built-in sandbox for physical verification (Step 4 of Plan)
    from dotenv import load_dotenv

    load_dotenv()

    logging.basicConfig(level=logging.INFO)

    async def main() -> None:
        logger.info("🚀 Starting REAL Fan-out Map-Reduce...")

        # Create a test state with a dummy user message to give the agents some context
        test_state = BetaState()
        test_state.shared.messages = [
            {
                "role": "user",
                "content": "Our Q3 campaign just ended. We spent $50k on ads, got 10k clicks, but only 50 conversions. Also the backend API crashed 5 times yesterday.",
            }
        ]

        # graph.run() returns (output, state) but sometimes with beta it's an object.
        # Let's use the object structure
        try:
            run_result = await beta_graph.run(deps=None, state=test_state)

            logger.info("=" * 40)
            logger.info(f"✅ Final Return Value: \n{run_result}")
            logger.info("-" * 40)
            logger.info(
                f"💰 Token ROI Verification: Input: {test_state.shared.input_tokens}, Output: {test_state.shared.output_tokens}, Model: {test_state.shared.model_used}"
            )
            logger.info("=" * 40)
        except Exception as e:
            logger.error(f"Execution crashed: {e}")

    asyncio.run(main())
