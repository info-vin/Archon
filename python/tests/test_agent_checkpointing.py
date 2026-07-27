"""
Unit tests for Phase 5.9.13 Agent DB Checkpointing & State Persistence.
"""

from unittest.mock import MagicMock

import pytest

from src.agents.checkpoint_manager import AgentCheckpointManager, CheckpointDTO
from src.agents.execution_engine import AgentExecutionEngine


@pytest.fixture
def mock_supabase():
    mock = MagicMock()
    # Mock table interface
    table_mock = MagicMock()
    mock.table.return_value = table_mock
    return mock, table_mock


@pytest.mark.asyncio
async def test_checkpoint_save_success(mock_supabase):
    supabase, table_mock = mock_supabase
    table_mock.upsert.return_value.execute.return_value.data = [{"id": "chk-123"}]

    mgr = AgentCheckpointManager(supabase_client=supabase)
    dto = CheckpointDTO(
        conversation_id="conv-001",
        step_index=1,
        agent_role="devbot",
        status="RUNNING",
        state_snapshot={"messages": [{"role": "user", "content": "Hello"}]},
    )

    checkpoint_id = await mgr.save_checkpoint(dto)
    assert checkpoint_id == "chk-123"
    table_mock.upsert.assert_called_once()


@pytest.mark.asyncio
async def test_checkpoint_load_latest_success(mock_supabase):
    supabase, table_mock = mock_supabase
    table_mock.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {
            "id": "chk-123",
            "conversation_id": "conv-001",
            "step_index": 2,
            "agent_role": "devbot",
            "status": "RUNNING",
            "state_snapshot": {"step": 2},
            "last_tool_call": None,
        }
    ]

    mgr = AgentCheckpointManager(supabase_client=supabase)
    res = await mgr.load_latest_checkpoint("conv-001")

    assert res is not None
    assert res.conversation_id == "conv-001"
    assert res.step_index == 2
    assert res.status == "RUNNING"


@pytest.mark.asyncio
async def test_execution_engine_non_sensitive_step(mock_supabase):
    supabase, table_mock = mock_supabase
    table_mock.upsert.return_value.execute.return_value.data = [{"id": "chk-101"}]

    chk_mgr = AgentCheckpointManager(supabase_client=supabase)
    engine = AgentExecutionEngine(checkpoint_mgr=chk_mgr)

    res = await engine.execute_step(
        conversation_id="conv-002",
        step_index=1,
        agent_role="librarian",
        state_snapshot={"task": "search"},
        tool_name="rag_search_knowledge_base",
        tool_args={"query": "test"},
    )

    assert res.status == "RUNNING"
    assert res.checkpoint_id == "chk-101"
