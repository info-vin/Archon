import logging
import os
import uuid
from typing import Any

import httpx
from pydantic_graph import Graph

from src.agents.checkpoint_manager import AgentCheckpointManager, CheckpointDTO
from src.server.services.shared_constants import WorkflowStatusEnum

from .nodes import DavidNode, DevBotNode, LibrarianNode, MarketBotNode, SummaryNode, SupervisorNode
from .state import SharedState
from .utils import _get_output

logger = logging.getLogger(__name__)

# --- 4. The Graph Orchestrator ---
workflow_graph = Graph(nodes=[SupervisorNode, MarketBotNode, LibrarianNode, SummaryNode, DevBotNode, DavidNode])

_START_NODE_MAP: dict[str, type[Any]] = {
    "supervisor": SupervisorNode,
    "marketbot": MarketBotNode,
    "librarian": LibrarianNode,
    "summary": SummaryNode,
    "devbot": DevBotNode,
    "david": DavidNode,
}


class WorkflowEngine:
    """Wrapper to run the graph, manage state, and persist/resume checkpoints."""

    async def _persist_checkpoint(
        self,
        checkpoint_mgr: AgentCheckpointManager | None,
        state: SharedState,
        agent_role: str,
        status: str,
    ) -> str | None:
        if checkpoint_mgr is None or not state.conversation_id:
            return None
        try:
            dto = CheckpointDTO(
                conversation_id=state.conversation_id,
                step_index=state.step_count,
                agent_role=agent_role,
                status=status,
                state_snapshot=state.model_dump(),
            )
            return await checkpoint_mgr.save_checkpoint(dto)
        except Exception as e:
            logger.warning(f"⚠️ Failed to persist workflow checkpoint ({state.conversation_id}): {e}")
            return None

    async def run_workflow(
        self,
        initial_prompt: str,
        task_type: str = "General",
        conversation_id: str | None = None,
        start_agent: str = "supervisor",
        checkpoint_mgr: AgentCheckpointManager | None = None,
    ) -> dict[str, Any]:
        conv_id = conversation_id or str(uuid.uuid4())
        state = SharedState(
            messages=[{"role": "user", "content": initial_prompt}],
            task_type=task_type,
            conversation_id=conv_id,
        )
        return await self._execute_graph(state, start_agent=start_agent, checkpoint_mgr=checkpoint_mgr)

    async def resume_from_checkpoint(
        self,
        conversation_id: str,
        checkpoint_mgr: AgentCheckpointManager | None = None,
    ) -> dict[str, Any]:
        """Restores SharedState from the latest Supabase checkpoint and resumes execution."""
        mgr = checkpoint_mgr or AgentCheckpointManager()
        dto = await mgr.load_latest_checkpoint(conversation_id)
        if not dto:
            return {
                "success": False,
                "error": f"No checkpoint found for conversation {conversation_id}",
                "step_count": 0,
                "messages": [],
                "conversation_id": conversation_id,
            }

        state = SharedState.model_validate(dto.state_snapshot)
        state.conversation_id = conversation_id
        state.status = WorkflowStatusEnum.RUNNING.value
        return await self._execute_graph(state, start_agent=dto.agent_role, checkpoint_mgr=mgr)

    async def _execute_graph(
        self,
        state: SharedState,
        start_agent: str = "supervisor",
        checkpoint_mgr: AgentCheckpointManager | None = None,
    ) -> dict[str, Any]:
        start_cls = _START_NODE_MAP.get(start_agent.lower().strip(), SupervisorNode)
        try:
            run_result = await workflow_graph.run(start_cls(), state=state)
            final_state = run_result.state

            # Phase 5.4 / 5.1.9: Fix Token Logging Gap with Fire-and-Forget Telemetry
            try:
                if final_state.input_tokens > 0 or final_state.output_tokens > 0:
                    import asyncio

                    async def log_telemetry() -> None:
                        server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
                        async with httpx.AsyncClient() as client:
                            payload = {
                                "model": final_state.model_used or "workflow-engine",
                                "provider": "google",
                                "input_tokens": final_state.input_tokens,
                                "output_tokens": final_state.output_tokens,
                                "context_type": "agentic_workflow",
                            }
                            server_host = os.getenv("ARCHON_SERVER_HOST") or os.getenv("ARCHON_HOST") or "127.0.0.1"
                            try:
                                await client.post(
                                    f"http://{server_host}:{server_port}/internal/stats/token-usage",
                                    json=payload,
                                    timeout=5.0,
                                )
                                logger.info("📊 Token usage logged via Internal API (Background Task)")
                            except Exception as e:
                                logger.warning(f"⚠️ Background telemetry failed: {e}")

                    # Await with a short timeout to ensure it completes before CLI process terminates
                    try:
                        await asyncio.wait_for(log_telemetry(), timeout=2.0)
                    except TimeoutError:
                        logger.warning("⚠️ Telemetry logging timed out (2.0s limit).")
                    except Exception as tele_err:
                        logger.warning(f"⚠️ Telemetry logging failed: {tele_err}")
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

            is_success = (
                "Supervisor Error:" not in final_res_str
                and "Circuit Breaker Tripped:" not in final_res_str
                and not final_res_str.startswith("Error:")
            )
            error_msg = None
            if not is_success:
                error_msg = final_res_str

            final_state.status = (
                WorkflowStatusEnum.COMPLETED.value if is_success else WorkflowStatusEnum.FAILED.value
            )
            last_role = (
                str(final_state.messages[-1].get("role", "supervisor")) if final_state.messages else "supervisor"
            )
            await self._persist_checkpoint(checkpoint_mgr, final_state, last_role, final_state.status)

            return {
                "success": is_success,
                "final_result": final_res_str if is_success else None,
                "error": error_msg,
                "step_count": final_state.step_count,
                "messages": final_state.messages,
                "conversation_id": final_state.conversation_id,
                "handoff_history": final_state.handoff_history,
            }
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            state.status = WorkflowStatusEnum.FAILED.value
            await self._persist_checkpoint(checkpoint_mgr, state, start_agent, WorkflowStatusEnum.FAILED.value)
            return {
                "success": False,
                "error": str(e),
                "step_count": state.step_count,
                "messages": state.messages,
                "conversation_id": state.conversation_id,
                "handoff_history": state.handoff_history,
            }
