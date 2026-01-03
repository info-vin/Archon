from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.agent_service import AgentService


@pytest.mark.asyncio
# Correctly patch the dependencies at their source, accounting for local imports.
@patch('src.server.services.projects.task_service.task_service', new_callable=AsyncMock)
@patch('src.server.services.agent_service.get_logger')
async def test_run_agent_task(mock_get_logger, mock_task_service):
    """
    Unit tests the AgentService.run_agent_task method.
    Verifies its actual behavior:
    1. It calls task_service.update_task to set status to 'processing'.
    2. It logs informational messages.
    """
    # --- Setup ---
    # Configure the mock logger returned by the mocked get_logger function
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    # Configure the mock for update_task to return a successful tuple
    mock_task_service.update_task.return_value = (True, {})

    agent_service = AgentService()
    task_id = "task-123"
    agent_id = "ai-test-agent"

    # --- Test Execution ---
    await agent_service.run_agent_task(task_id, agent_id)

    # --- Assertions ---
    # 1. Verify logger calls
    assert mock_logger.info.call_count == 3
    mock_logger.info.assert_any_call(
        f"AI agent '{agent_id}' has been notified to start working on task '{task_id}'."
    )
    mock_logger.info.assert_any_call(
        f"Task '{task_id}' status updated to 'processing' by agent '{agent_id}'."
    )
    mock_logger.info.assert_any_call(
        f"AI agent '{agent_id}' finished its work for task '{task_id}'."
    )

    # 2. Verify that task_service.update_task was called correctly
    mock_task_service.update_task.assert_awaited_once_with(
        task_id, {"status": "processing", "assignee": agent_id}
    )

@pytest.mark.asyncio
@patch('src.server.services.projects.task_service.task_service', new_callable=AsyncMock)
@patch('src.server.services.agent_service.get_logger')
async def test_run_agent_task_fails_to_update(mock_get_logger, mock_task_service):
    """
    Tests that if updating the task status fails, an error is logged.
    """
    # --- Setup ---
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    # Configure the mock to return a failure tuple
    mock_task_service.update_task.return_value = (False, {"error": "DB down"})

    agent_service = AgentService()
    task_id = "task-456"
    agent_id = "ai-failing-agent"

    # --- Test Execution ---
    await agent_service.run_agent_task(task_id, agent_id)

    # --- Assertions ---
    # Verify the error log call
    mock_logger.error.assert_called_once_with(
        f"Failed to update task '{task_id}' status to 'processing': DB down"
    )
    # The final "finished" log should still be called as the error is not re-raised
    mock_logger.info.assert_called_with(
        f"AI agent '{agent_id}' finished its work for task '{task_id}'."
    )


@pytest.mark.asyncio
@patch('src.server.services.agent_service.asyncio.create_subprocess_shell')
@patch('src.server.services.agent_service.get_logger')
async def test_run_command_success(mock_get_logger, mock_subprocess):
    """
    Test run_command_with_self_healing when command succeeds.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    # Mock subprocess success
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"success output", b"")
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process

    agent_service = AgentService()
    success, output = await agent_service.run_command_with_self_healing("echo test")

    assert success is True
    assert output == "success output"
    mock_logger.info.assert_called_with("Command 'echo test' succeeded.")


@pytest.mark.asyncio
@patch('src.server.services.agent_service.credential_service')
@patch('src.server.services.agent_service.get_llm_client')
@patch('src.server.services.agent_service.asyncio.create_subprocess_shell')
@patch('src.server.services.agent_service.get_logger')
async def test_run_command_failure_triggers_healing(
    mock_get_logger, mock_subprocess, mock_get_llm, mock_credential_service
):
    """
    Test run_command_with_self_healing when command fails.
    Verifies that it calls the LLM for analysis.
    """
    mock_logger = MagicMock()
    mock_get_logger.return_value = mock_logger

    # Mock subprocess failure
    mock_process = AsyncMock()
    mock_process.communicate.return_value = (b"", b"Error: command failed")
    mock_process.returncode = 1
    mock_subprocess.return_value = mock_process

    # Mock Credential Service
    mock_credential_service.get_active_provider = AsyncMock(return_value={"chat_model": "gpt-4-test"})

    # Mock LLM Client
    mock_client = AsyncMock()
    mock_get_llm.return_value.__aenter__.return_value = mock_client

    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="Suggested Fix: Check syntax"))]
    mock_client.chat.completions.create.return_value = mock_response

    agent_service = AgentService()
    success, output = await agent_service.run_command_with_self_healing("failing_cmd")

    assert success is False
    assert "Self-Healing Analysis" in output
    assert "Suggested Fix: Check syntax" in output

    # Verify LLM was called
    mock_client.chat.completions.create.assert_awaited_once()
    # Verify logger warned about failure
    mock_logger.warning.assert_called_with("Command 'failing_cmd' failed with exit code 1.")
