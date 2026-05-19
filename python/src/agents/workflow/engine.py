import logging
import os
from typing import Any

import httpx
from pydantic_graph import Graph

from .nodes import DavidNode, DevBotNode, LibrarianNode, MarketBotNode, SummaryNode, SupervisorNode
from .state import SharedState
from .utils import _get_output

logger = logging.getLogger(__name__)

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

            # Phase 5.4 / 5.1.9: Fix Token Logging Gap with Fire-and-Forget Telemetry
            try:
                if final_state.input_tokens > 0 or final_state.output_tokens > 0:
                    import asyncio

                    async def log_telemetry():
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
                            try:
                                await client.post(
                                    f"http://{server_host}:{server_port}/internal/stats/token-usage",
                                    json=payload,
                                    timeout=5.0,
                                )
                                logger.info("📊 Token usage logged via Internal API (Background Task)")
                            except Exception as e:
                                logger.warning(f"⚠️ Background telemetry failed: {e}")

                    # Fire and forget the telemetry task
                    asyncio.create_task(log_telemetry())
            except Exception as e:
                logger.warning(f"⚠️ Failed to initiate background token logging: {e}")

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
