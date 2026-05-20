import asyncio
import logging
import os
import time

from dotenv import load_dotenv

from src.agents.workflow.engine import WorkflowEngine
from src.agents.workflow.engine_beta_graph import BetaState, beta_graph

logging.basicConfig(level=logging.WARNING, format="%(message)s")
logger = logging.getLogger("comparison")
logger.setLevel(logging.INFO)

async def test_linear_engine(prompt: str):
    logger.info("=== Starting Linear Engine Test ===")
    start_time = time.time()

    os.environ["SUPERVISOR_AGENT_MODEL"] = "gemini-3.1-flash-lite"
    os.environ["WORKER_AGENT_MODEL"] = "gemini-3.1-flash-lite"

    engine = WorkflowEngine()
    result = await engine.run_workflow(initial_prompt=prompt, task_type="Marketing Data Deep Dive")

    end_time = time.time()

    logger.info(f"Linear Engine finished in {end_time - start_time:.2f} seconds")
    logger.info(f"Linear Engine Steps: {result.get('step_count')}")
    return end_time - start_time, result.get("step_count")

async def test_fanout_engine(prompt: str):
    logger.info("=== Starting Fan-out Beta Engine Test ===")
    start_time = time.time()

    state = BetaState()
    state.shared.messages = [{"role": "user", "content": prompt}]

    try:
        run_result = await beta_graph.run(deps=None, state=state)
        # Using the fix we applied to the graph file where we don't unpack
        final_state = run_result.state

        end_time = time.time()

        logger.info(f"Fan-out Engine finished in {end_time - start_time:.2f} seconds")
        logger.info(f"Fan-out Token ROI: Input: {final_state.shared.input_tokens}, Output: {final_state.shared.output_tokens}")
        return end_time - start_time, final_state.shared.input_tokens, final_state.shared.output_tokens
    except Exception as e:
        logger.error(f"Fan-out Engine failed: {e}")
        return 0, 0, 0

async def main():
    load_dotenv()

    prompt = "Please analyze the Q3 campaign results. We spent $50k on ads, got 10k clicks, but only 50 conversions. Also the backend API crashed 5 times yesterday. I need insights on sales, marketing, and system stability."

    linear_time, linear_steps = await test_linear_engine(prompt)
    fanout_time, fanout_in, fanout_out = await test_fanout_engine(prompt)

    logger.info("\n\n" + "="*50)
    logger.info("📊 ARCHON WORKFLOW ENGINE COMPARISON")
    logger.info("="*50)
    logger.info("【架構差異】")
    logger.info("- Linear (v1) : 迴圈決策 (Supervisor -> Worker -> Supervisor -> ...)")
    logger.info("- Fan-out (v2): Map-Reduce (發散 -> 並行執行 -> Join Barrier -> 聚合)")
    logger.info("")
    logger.info("【效能數據】")
    logger.info(f"- Linear Engine Time : {linear_time:.2f} seconds ({linear_steps} 狀態機躍遷)")
    logger.info(f"- Fan-out Engine Time: {fanout_time:.2f} seconds (3 Worker 並發 + 1 Supervisor)")
    logger.info(f"- Token 總消耗 (v2)  : Input {fanout_in}, Output {fanout_out}")
    if linear_time > 0 and fanout_time > 0:
        if linear_time > fanout_time:
            speedup = ((linear_time - fanout_time) / linear_time) * 100
            logger.info(f"🚀 速度提升: 快了 {speedup:.1f}%")
        else:
            overhead = ((fanout_time - linear_time) / linear_time) * 100
            logger.info(f"⏱️ 延遲增加: 慢了 {overhead:.1f}%")
    logger.info("="*50)

if __name__ == "__main__":
    asyncio.run(main())
