"""
Experimental GraphBuilder Implementation (Phase 5.1.10 / Fan-out)
This module explores the pydantic_graph.beta.GraphBuilder API for parallel execution (Fan-out)
and map-reduce patterns. It is kept isolated from the production `engine.py` to prevent regressions.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from pydantic_graph.beta import GraphBuilder, StepContext

logger = logging.getLogger(__name__)

# --- Experimental Beta State ---
@dataclass
class BetaState:
    history: list[dict[str, Any]] = field(default_factory=list)
    map_results: dict[str, str] = field(default_factory=dict)
    
builder = GraphBuilder(state_type=BetaState, output_type=str)

# 3. Inject Semaphore: asyncio.Semaphore(2) for Free-Tier 429 protection
sem = asyncio.Semaphore(2)

@builder.step
async def supervisor_step(ctx: StepContext[BetaState, None, None]) -> list[str]:
    """
    Supervisor returning a list of targets to map over.
    This triggers the Map phase.
    """
    logger.info("🧪 [Beta Graph] Supervisor thinking... Dispatching to workers.")
    return ["sales", "marketing", "system"]

@builder.step
async def worker_step(ctx: StepContext[BetaState, None, str]) -> dict[str, str]:
    """
    Worker node for Fan-out. Processes individual targets concurrently.
    """
    # In mapped nodes using pydantic_graph.beta, ctx.inputs contains the individual mapped item
    target = ctx.inputs 
    
    async with sem:
        logger.info(f"👷 [Worker] Processing target: {target}")
        await asyncio.sleep(0.5) # Simulated jitter/processing
        
        # 4. Mock Verification Data (Phase 5.1.10 step 4)
        mock_data = {
            "sales": "Alice's Sales Report: +15% revenue.",
            "marketing": "Bob's Marketing Report: High engagement.",
            "system": "System Report: Token usage nominal."
        }
        
        result = mock_data.get(target, "Unknown report")
        logger.info(f"👷 [Worker] Completed target: {target}")
        return {target: result}

def reduce_results(current: dict[str, str], incoming: dict[str, str]) -> dict[str, str]:
    """Reducer function for the Join node (Reduce phase)"""
    current.update(incoming)
    return current

# Create the Join node
join_node = builder.join(reduce_results, initial_factory=dict)

@builder.step
async def final_summary_step(ctx: StepContext[BetaState, None, dict[str, str]]) -> str:
    """
    Final node that aggregates the mapped results into a summary.
    """
    logger.info("📊 [Beta Graph] Generating Final Summary from Map-Reduce...")
    
    # Store aggregated results in state
    ctx.state.map_results = ctx.inputs
    
    summary_lines = [f"- {k}: {v}" for k, v in ctx.inputs.items()]
    summary = "Executive Summary:\n" + "\n".join(summary_lines)
    logger.info(f"Final Output:\n{summary}")
    return summary

# Wire up the edges for fan-out
# start -> supervisor_step -> [worker_step (map)] -> join_node -> final_summary_step -> END
builder.add_edge(source=builder.start_node, destination=supervisor_step)
builder.add_mapping_edge(source=supervisor_step, map_to=worker_step)
builder.add_edge(source=worker_step, destination=join_node)
builder.add_edge(source=join_node, destination=final_summary_step)
builder.add_edge(source=final_summary_step, destination=builder.end_node)

beta_graph = builder.build()

if __name__ == "__main__":
    # Built-in sandbox for physical verification (Step 4 of Plan)
    logging.basicConfig(level=logging.INFO)
    async def main():
        logger.info("🚀 Starting Fan-out Map-Reduce PoC...")
        result = await beta_graph.run(state=BetaState())
        logger.info(f"✅ Run Completed. Final Return Value: \n{result}")
        
    asyncio.run(main())
