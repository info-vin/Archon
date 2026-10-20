from unittest.mock import MagicMock, patch

from src.agents.workflow.nodes import SupervisorNode
from src.agents.workflow.state import SharedState
from src.server.prompts.pm_prompts import WORKFLOW_SUPERVISOR_DAILY, WORKFLOW_WORKER_SUMMARY
from src.server.services.shared_constants import PromptNameEnum, TaskFeatureEnum


def test_workflow_constants_and_prompts():
    """Verify that PromptNameEnum and default prompt contracts are aligned."""
    assert PromptNameEnum.WORKFLOW_SUPERVISOR_DAILY == "WORKFLOW_SUPERVISOR_DAILY"
    assert PromptNameEnum.WORKFLOW_WORKER_SUMMARY == "WORKFLOW_WORKER_SUMMARY"
    assert "Markdown" in WORKFLOW_WORKER_SUMMARY
    assert "Charlie" in WORKFLOW_SUPERVISOR_DAILY
    assert "marketbot" in WORKFLOW_SUPERVISOR_DAILY
    assert "devbot" in WORKFLOW_SUPERVISOR_DAILY


@patch("src.server.utils.get_supabase_client")
@patch("os.getenv")
@patch("src.agents.workflow.nodes.Agent")
@patch("src.agents.workflow.nodes._run_agent_with_retry")
def test_supervisor_node_normalized_flow_matching(mock_run_agent, mock_agent_class, mock_getenv, mock_get_supabase):
    """Test that SupervisorNode matches 'Daily Executive Summary' regardless of case or underscores."""
    mock_getenv.return_value = "gemini-3.5-flash-lite"

    mock_supabase = MagicMock()
    mock_get_supabase.return_value = mock_supabase

    mock_db_flows = [
        {
            "workflow_type": "Daily Executive Summary",
            "supervisor_prompt_name": "WORKFLOW_SUPERVISOR_DAILY",
            "node_routing": {"bob": "MarketBotNode", "devbot": "DevBotNode"},
        }
    ]

    mock_query = MagicMock()
    mock_query.select.return_value = mock_query
    mock_supabase.table.return_value = mock_query

    # Mock execute_query on BaseRepository
    with patch("src.server.repositories.base_repository.BaseRepository.execute_query") as mock_exec:
        mock_exec.return_value = (True, {"data": mock_db_flows})

        # Test with task_type = "daily_executive_summary" (lowercase with underscore)
        state = SharedState(
            messages=[{"role": "user", "content": "Please run daily summary"}],
            task_type=TaskFeatureEnum.DAILY_EXECUTIVE_SUMMARY.value,
        )

        ctx = MagicMock()
        ctx.state = state

        # Mock agent decision to "end"
        mock_decision = MagicMock()
        mock_decision.next_node = "end"
        mock_decision.reasoning = "done"

        mock_result = MagicMock()
        mock_run_agent.return_value = mock_result

        with patch("src.agents.workflow.nodes._get_output", return_value=mock_decision):
            node = SupervisorNode()
            import asyncio

            end_result = asyncio.run(node.run(ctx))
            assert end_result is not None

            # Verify that agent was initialized with WORKFLOW_SUPERVISOR_DAILY
            mock_agent_class.assert_called_once()
            call_kwargs = mock_agent_class.call_args[1]
            assert "Charlie" in call_kwargs["system_prompt"]
            assert "每日執行摘要" in call_kwargs["system_prompt"]
            assert state.final_result == "Workflow completed successfully."
