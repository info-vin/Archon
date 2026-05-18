
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import patch


async def test_worker_flow():
    print("🧪 Testing Worker Queue Flow...")

    # 1. Setup Mock objects
    mock_task_service = MagicMock()
    mock_agent_service = MagicMock()

    # Mock task_service.list_tasks to return a dispatched task
    task_id = "test-task-123"
    agent_id = "test-agent-456"

    mock_task_service.list_tasks = AsyncMock(side_effect=[
        (True, {"tasks": [{"id": task_id, "assignee": agent_id}]}),
        (True, {"tasks": []}) # Second poll returns empty
    ])

    mock_task_service.update_task = AsyncMock(return_value=(True, {}))
    mock_agent_service.run_agent_task = AsyncMock(return_value=None)

    # 2. Patch services and run process_queued_tasks
    with patch("src.server.services.client_manager.get_supabase_client", return_value=MagicMock()), \
         patch("src.server.services.projects.task_service.task_service", mock_task_service), \
         patch("src.server.services.agent_service.agent_service", mock_agent_service):

        from src.server.services.system.worker_service import worker_service

        await worker_service._process_queued_tasks()

        # 3. Assertions
        # Check if task was marked as processing
        mock_task_service.update_task.assert_any_call(task_id, {"status": "processing"})

        # Check if agent_service.run_agent_task was called with immediate=True
        mock_agent_service.run_agent_task.assert_called_once_with(task_id=task_id, agent_id=agent_id, immediate=True)

    print("✅ Worker Flow Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_worker_flow())

