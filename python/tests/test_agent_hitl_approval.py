"""
Unit tests for Phase 5.9.13 Agent Human-in-the-Loop (HITL) tool approval workflow.
"""

from unittest.mock import MagicMock

import pytest

from src.agents.approval_manager import AgentApprovalManager
from src.agents.checkpoint_manager import AgentCheckpointManager
from src.agents.execution_engine import AgentExecutionEngine


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    table_mock = MagicMock()
    mock.table.return_value = table_mock
    return mock, table_mock


@pytest.mark.asyncio
async def test_execution_engine_sensitive_tool_interception(mock_supabase):
    supabase, table_mock = mock_supabase
    # Mock upsert checkpoint & insert approval
    table_mock.upsert.return_value.execute.return_value.data = [{"id": "chk-999"}]
    table_mock.insert.return_value.execute.return_value.data = [{"approval_id": "app-777"}]

    chk_mgr = AgentCheckpointManager(supabase_client=supabase)
    app_mgr = AgentApprovalManager(supabase_client=supabase)
    engine = AgentExecutionEngine(checkpoint_mgr=chk_mgr, approval_mgr=app_mgr)

    res = await engine.execute_step(
        conversation_id="conv-sensitive-01",
        step_index=3,
        agent_role="devbot",
        state_snapshot={"command": "rm -rf /"},
        tool_name="execute_shell_command",
        tool_args={"cmd": "rm -rf /"},
    )

    assert res["status"] == "SUSPENDED_WAITING_FOR_APPROVAL"
    assert res["checkpoint_id"] == "chk-999"
    assert res["approval_id"] == "app-777"
    assert res["tool_name"] == "execute_shell_command"


@pytest.mark.asyncio
async def test_approval_manager_review_approved(mock_supabase):
    supabase, table_mock = mock_supabase
    table_mock.update.return_value.eq.return_value.execute.return_value.data = [
        {
            "approval_id": "app-777",
            "conversation_id": "conv-sensitive-01",
            "checkpoint_id": "chk-999",
            "tool_name": "execute_shell_command",
            "tool_args": {"cmd": "ls"},
            "status": "APPROVED",
            "reviewer_id": "admin_user",
            "review_reason": "Approved",
        }
    ]

    app_mgr = AgentApprovalManager(supabase_client=supabase)
    res = await app_mgr.review_approval("app-777", approved=True, reviewer_id="admin_user")

    assert res.status == "APPROVED"
    assert res.reviewer_id == "admin_user"
