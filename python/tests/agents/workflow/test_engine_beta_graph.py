from unittest.mock import AsyncMock, patch

import pytest

from src.agents.workflow.engine_beta_graph import BetaState, beta_graph
from src.agents.workflow.state import SharedState


@pytest.mark.asyncio
@patch("src.agents.workflow.engine_beta_graph._run_agent_with_retry", new_callable=AsyncMock)
@patch("src.agents.workflow.engine_beta_graph._accumulate_usage")
async def test_beta_graph_fan_out_success(mock_accumulate, mock_run_agent):
    """
    Test the happy path of the experimental Beta graph.
    Verifies that all 3 workers and 1 final supervisor are executed successfully.
    """
    class MockResult:
        def __init__(self, data):
            self.data = data

    async def side_effect(agent, prompt, *args, **kwargs):
        if "reports from the sub-agents" in prompt:
            return MockResult("Final Executive Summary")
        elif "SALES" in prompt.upper():
            return MockResult("Sales insights")
        elif "MARKETING" in prompt.upper():
            return MockResult("Marketing insights")
        elif "SYSTEM" in prompt.upper():
            return MockResult("System insights")
        else:
            return MockResult("Final Executive Summary")

    mock_run_agent.side_effect = side_effect

    test_state = BetaState(shared=SharedState())
    test_state.shared.messages = [{"role": "user", "content": "Test context"}]

    run_result = await beta_graph.run(deps=None, state=test_state)

    output = run_result.output if hasattr(run_result, "output") else run_result

    assert "Final Executive Summary" in str(output)

    # 3 workers (sales, marketing, system) + 1 final summary = 4 LLM calls
    assert mock_run_agent.call_count == 4
    assert mock_accumulate.call_count == 4


@pytest.mark.asyncio
@patch("src.agents.workflow.engine_beta_graph._run_agent_with_retry", new_callable=AsyncMock)
@patch("src.agents.workflow.engine_beta_graph._accumulate_usage")
async def test_beta_graph_worker_failure_handling(mock_accumulate, mock_run_agent):
    """
    Test partial failure in the Fan-out step.
    Verifies that the graph continues gracefully if one worker fails.
    """
    class MockResult:
        def __init__(self, data):
            self.data = data

    async def side_effect(agent, prompt, *args, **kwargs):
        if "reports from the sub-agents" in prompt:
            return MockResult("Partial Summary")
        elif "MARKETING" in prompt.upper():
            raise ValueError("Simulated marketing LLM timeout")
        elif "SALES" in prompt.upper() or "SYSTEM" in prompt.upper():
            return MockResult("Success")
        else:
            return MockResult("Partial Summary")

    mock_run_agent.side_effect = side_effect

    test_state = BetaState(shared=SharedState())
    test_state.shared.messages = [{"role": "user", "content": "Test context"}]

    run_result = await beta_graph.run(deps=None, state=test_state)

    output = run_result.output if hasattr(run_result, "output") else run_result

    assert "Partial Summary" in str(output)

    # Calls: 3 workers (1 failed) + 1 final summary = 4 total attempts
    assert mock_run_agent.call_count == 4
    # Accumulate should only be called for successful agent runs (sales, system, final) = 3 times
    assert mock_accumulate.call_count == 3


@pytest.mark.asyncio
@patch("src.agents.workflow.engine_beta_graph._run_agent_with_retry", new_callable=AsyncMock)
async def test_beta_graph_token_roi_accumulation(mock_run_agent):
    """
    Test that Token ROI accumulation correctly adds up tokens concurrently.
    Verifies that multi-threaded writes to SharedState are safe in this context.
    """
    class MockUsage:
        request_tokens = 10
        response_tokens = 5

    class MockResult:
        def __init__(self, data):
            self.data = data
        def usage(self):
            return MockUsage()

    mock_run_agent.return_value = MockResult("Mocked Output")

    test_state = BetaState(shared=SharedState())
    test_state.shared.messages = [{"role": "user", "content": "Test context"}]

    await beta_graph.run(deps=None, state=test_state)

    # 3 workers + 1 supervisor = 4 calls. Each uses 10 input, 5 output.
    # Total expected: 40 input, 20 output.
    assert test_state.shared.input_tokens == 40
    assert test_state.shared.output_tokens == 20
    assert test_state.shared.model_used == "gemini-3.1-flash-lite"
