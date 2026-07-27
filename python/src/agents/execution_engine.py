"""
Agent Execution Engine with Checkpointing & HITL for Phase 5.9.13.

Integrates state persistence (AgentCheckpointManager) and HITL approval gates (AgentApprovalManager).
"""

import logging
from typing import Any

from src.server.models.agent_models import ExecutionStepResult, ResumeExecutionResult

from .approval_manager import AgentApprovalManager, ApprovalRequestDTO
from .checkpoint_manager import AgentCheckpointManager, CheckpointDTO

logger = logging.getLogger(__name__)

# Default list of tools categorized as high-risk needing HITL approval if not overridden in settings
DEFAULT_SENSITIVE_TOOLS = {
    "execute_shell_command",
    "apply_modification",
    "delete_file",
    "deploy_to_production",
    "drop_database_table",
}


class AgentExecutionEngine:
    """Agent execution orchestrator with state checkpointing and HITL interception."""

    def __init__(
        self,
        checkpoint_mgr: AgentCheckpointManager | None = None,
        approval_mgr: AgentApprovalManager | None = None,
    ) -> None:
        self.checkpoint_mgr = checkpoint_mgr or AgentCheckpointManager()
        self.approval_mgr = approval_mgr or AgentApprovalManager()

    def _get_sensitive_tools(self) -> set[str]:
        """Dynamically fetch sensitive tool names from SettingsService SSOT."""
        try:
            from src.server.services.settings_service import SettingsService

            settings = SettingsService()
            custom_tools = settings.get_setting("AGENT_SENSITIVE_TOOLS")
            if custom_tools and isinstance(custom_tools, str):
                import json

                parsed = json.loads(custom_tools)
                if isinstance(parsed, list):
                    return set(parsed)
        except Exception as e:
            logger.debug(f"[ExecutionEngine] Using default sensitive tools fallback: {e}")
        return DEFAULT_SENSITIVE_TOOLS

    async def execute_step(
        self,
        conversation_id: str,
        step_index: int,
        agent_role: str,
        state_snapshot: dict[str, Any],
        tool_name: str | None = None,
        tool_args: dict[str, Any] | None = None,
    ) -> ExecutionStepResult:
        """
        Executes a single step for an Agent.
        - If tool_name is sensitive, saves a PENDING_APPROVAL checkpoint and creates HITL request.
        - Otherwise, saves a RUNNING checkpoint and proceeds.
        """
        last_tool = None
        if tool_name:
            last_tool = {"name": tool_name, "args": tool_args or {}}

        # Check if sensitive tool call
        sensitive_tools = self._get_sensitive_tools()
        if tool_name and tool_name in sensitive_tools:
            logger.warning(f"[ExecutionEngine] Intercepted sensitive tool '{tool_name}' for conv {conversation_id}")

            # Save checkpoint with PENDING_APPROVAL status
            checkpoint_id = await self.checkpoint_mgr.save_checkpoint(
                CheckpointDTO(
                    conversation_id=conversation_id,
                    step_index=step_index,
                    agent_role=agent_role,
                    status="PENDING_APPROVAL",
                    state_snapshot=state_snapshot,
                    last_tool_call=last_tool,
                )
            )

            # Create HITL Approval Request
            approval_id = await self.approval_mgr.create_approval_request(
                ApprovalRequestDTO(
                    conversation_id=conversation_id,
                    checkpoint_id=checkpoint_id,
                    tool_name=tool_name,
                    tool_args=tool_args or {},
                    risk_level="HIGH",
                    status="PENDING",
                )
            )

            return ExecutionStepResult(
                status="SUSPENDED_WAITING_FOR_APPROVAL",
                checkpoint_id=checkpoint_id,
                step_index=step_index,
                approval_id=approval_id,
                tool_name=tool_name,
                tool_args=tool_args,
                message=f"Sensitive tool '{tool_name}' requires human approval before execution.",
            )

        # Non-sensitive tool or standard step -> Save RUNNING checkpoint
        checkpoint_id = await self.checkpoint_mgr.save_checkpoint(
            CheckpointDTO(
                conversation_id=conversation_id,
                step_index=step_index,
                agent_role=agent_role,
                status="RUNNING",
                state_snapshot=state_snapshot,
                last_tool_call=last_tool,
            )
        )

        return ExecutionStepResult(
            status="RUNNING",
            checkpoint_id=checkpoint_id,
            step_index=step_index,
            message="Step executed and state checkpoint saved successfully.",
        )

    async def resume_execution(self, conversation_id: str) -> ResumeExecutionResult:
        """Resumes agent execution from the latest checkpoint snapshot."""
        latest = await self.checkpoint_mgr.load_latest_checkpoint(conversation_id)
        if not latest:
            raise ValueError(f"No checkpoint found for conversation ID {conversation_id}")

        if latest.status == "PENDING_APPROVAL":
            return ResumeExecutionResult(
                status="PENDING_APPROVAL",
                conversation_id=conversation_id,
                step_index=latest.step_index,
                message="Agent execution is still waiting for human approval.",
            )

        logger.info(f"[ExecutionEngine] Resuming conv {conversation_id} from step {latest.step_index}")
        return ResumeExecutionResult(
            status="RESUMED",
            conversation_id=conversation_id,
            step_index=latest.step_index,
            state_snapshot=latest.state_snapshot,
            agent_role=latest.agent_role,
            message=f"Successfully resumed from step {latest.step_index}.",
        )
