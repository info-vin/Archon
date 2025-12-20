from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.server.services.projects.task_service import (  # Ensure task_service singleton is imported
    TaskService,
)


# Mock Supabase client for all tests
@pytest.fixture
def mock_supabase_client():
    with patch('src.server.utils.get_supabase_client') as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        yield mock_client

# Test TaskService instance
@pytest.fixture
def test_task_service(mock_supabase_client):
    # Ensure a fresh instance for tests that might modify internal state
    return TaskService(supabase_client=mock_supabase_client)

@pytest.mark.asyncio
async def test_update_task_status_from_agent_success(test_task_service, mock_supabase_client):
    """Test successful status update from an assigned agent."""
    test_task_id = "test-task-uuid"
    test_agent_id = "ai-researcher-1"
    new_status = "doing"

    # Mock get_task to return a task assigned to the test_agent_id
    test_task = {
        "id": test_task_id,
        "assignee": test_agent_id,
        "status": "todo",
        "attachments": []
    }
    test_task_service.get_task = AsyncMock(return_value=(True, {"task": test_task}))
    test_task_service.update_task = AsyncMock(return_value=(True, {"task": {**test_task, "status": new_status}}))

    success, result = await test_task_service.update_task_status_from_agent(
        task_id=test_task_id, new_status=new_status, agent_id=test_agent_id
    )

    assert success is True
    assert result["task"]["status"] == new_status
    test_task_service.get_task.assert_called_once_with(test_task_id)
    test_task_service.update_task.assert_called_once_with(
        test_task_id, {"status": new_status, "assignee": test_agent_id}
    )

@pytest.mark.asyncio
async def test_update_task_status_from_agent_unauthorized(test_task_service, mock_supabase_client):
    """Test status update failure from an unauthorized agent."""
    test_task_id = "test-task-uuid"
    assigned_agent_id = "ai-researcher-1"
    unauthorized_agent_id = "ai-qa-agent-2"
    new_status = "doing"

    test_task = {
        "id": test_task_id,
        "assignee": assigned_agent_id,
        "status": "todo",
        "attachments": []
    }
    test_task_service.get_task = AsyncMock(return_value=(True, {"task": test_task}))
    test_task_service.update_task = AsyncMock() # Should not be called

    success, result = await test_task_service.update_task_status_from_agent(
        task_id=test_task_id, new_status=new_status, agent_id=unauthorized_agent_id
    )

    assert success is False
    assert "not authorized" in result["error"]
    test_task_service.get_task.assert_called_once_with(test_task_id)
    test_task_service.update_task.assert_not_called()

@pytest.mark.asyncio
async def test_save_agent_output_success_empty_attachments(test_task_service, mock_supabase_client):
    """Test successful saving of agent output to an empty attachments list."""
    test_task_id = "test-task-uuid"
    test_agent_id = "ai-researcher-1"
    test_output = {"summary": "Task completed successfully", "results": [1, 2, 3]}

    test_task = {
        "id": test_task_id,
        "assignee": test_agent_id,
        "status": "processing",
        "attachments": [] # Empty attachments
    }
    test_task_service.get_task = AsyncMock(return_value=(True, {"task": test_task}))

    # Mock the update_task call's return value for the new attachments
    expected_attachments_update = [
        {"agent_id": test_agent_id, "output": test_output, "timestamp": Any} # Timestamp is dynamic
    ]
    test_task_service.update_task = AsyncMock(
        return_value=(True, {"task": {**test_task, "attachments": expected_attachments_update}})
    )

    success, result = await test_task_service.save_agent_output(
        task_id=test_task_id, output=test_output, agent_id=test_agent_id
    )

    assert success is True
    assert "attachments" in result["task"]
    assert len(result["task"]["attachments"]) == 1
    assert result["task"]["attachments"][0]["agent_id"] == test_agent_id
    assert result["task"]["attachments"][0]["output"] == test_output
    test_task_service.get_task.assert_called_once_with(test_task_id)

    # Assert update_task was called with the correct structure (ignoring dynamic timestamp)
    call_args, _ = test_task_service.update_task.call_args_list[0]
    updated_task_id, update_fields = call_args
    assert updated_task_id == test_task_id
    assert "attachments" in update_fields
    assert len(update_fields["attachments"]) == 1
    assert update_fields["attachments"][0]["agent_id"] == test_agent_id
    assert update_fields["attachments"][0]["output"] == test_output
    assert "timestamp" in update_fields["attachments"][0]


@pytest.mark.asyncio
async def test_save_agent_output_success_existing_attachments(test_task_service, mock_supabase_client):
    """Test successful saving of agent output to existing attachments."""
    test_task_id = "test-task-uuid"
    test_agent_id = "ai-researcher-1"
    test_output = {"step": 2, "message": "More work done"}
    existing_attachment = {"type": "manual", "content": "Initial note"}

    test_task = {
        "id": test_task_id,
        "assignee": test_agent_id,
        "status": "processing",
        "attachments": [existing_attachment] # Existing attachments
    }
    test_task_service.get_task = AsyncMock(return_value=(True, {"task": test_task}))

    # Mock the update_task call's return value for the new attachments
    expected_attachments_update = [
        existing_attachment,
        {"agent_id": test_agent_id, "output": test_output, "timestamp": Any}
    ]
    test_task_service.update_task = AsyncMock(
        return_value=(True, {"task": {**test_task, "attachments": expected_attachments_update}})
    )

    success, result = await test_task_service.save_agent_output(
        task_id=test_task_id, output=test_output, agent_id=test_agent_id
    )

    assert success is True
    assert "attachments" in result["task"]
    assert len(result["task"]["attachments"]) == 2
    assert result["task"]["attachments"][0] == existing_attachment
    assert result["task"]["attachments"][1]["agent_id"] == test_agent_id
    assert result["task"]["attachments"][1]["output"] == test_output
    test_task_service.get_task.assert_called_once_with(test_task_id)

    # Assert update_task was called with the correct structure (ignoring dynamic timestamp)
    call_args, _ = test_task_service.update_task.call_args_list[0]
    updated_task_id, update_fields = call_args
    assert updated_task_id == test_task_id
    assert "attachments" in update_fields
    assert len(update_fields["attachments"]) == 2
    assert update_fields["attachments"][0] == existing_attachment
    assert update_fields["attachments"][1]["agent_id"] == test_agent_id
    assert update_fields["attachments"][1]["output"] == test_output
    assert "timestamp" in update_fields["attachments"][1]


@pytest.mark.asyncio
async def test_save_agent_output_unauthorized(test_task_service, mock_supabase_client):
    """Test saving agent output failure from an unauthorized agent."""
    test_task_id = "test-task-uuid"
    assigned_agent_id = "ai-researcher-1"
    unauthorized_agent_id = "ai-qa-agent-2"
    test_output = {"error": "Access denied"}

    test_task = {
        "id": test_task_id,
        "assignee": assigned_agent_id,
        "status": "processing",
        "attachments": []
    }
    test_task_service.get_task = AsyncMock(return_value=(True, {"task": test_task}))
    test_task_service.update_task = AsyncMock() # Should not be called

    success, result = await test_task_service.save_agent_output(
        task_id=test_task_id, output=test_output, agent_id=unauthorized_agent_id
    )

    assert success is False
    assert "not authorized" in result["error"]
    test_task_service.get_task.assert_called_once_with(test_task_id)
    test_task_service.update_task.assert_not_called()

