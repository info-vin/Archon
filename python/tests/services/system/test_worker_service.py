from unittest.mock import AsyncMock, patch

import pytest

from src.server.services.system.worker_service import WorkerService


@pytest.fixture
def mock_task_service():
    with patch("src.server.services.system.worker_service.task_service") as mock_ts:
        mock_ts.list_tasks = AsyncMock()
        mock_ts.update_task = AsyncMock()
        yield mock_ts

@pytest.mark.asyncio
async def test_recover_zombie_tasks_auto_retry(mock_task_service):
    # Setup mock returns: one zombie task with retry_count < 3
    mock_task_service.list_tasks.side_effect = [
        # Call 1: processing
        (True, {"tasks": [{"id": "task-1", "retry_count": 0, "description": "Original desc"}]}),
        # Call 2: doing
        (True, {"tasks": []})
    ]

    worker = WorkerService()
    await worker._recover_zombie_tasks()

    # Assert update_task was called with dispatched and retry_count=1
    mock_task_service.update_task.assert_called_once()
    args, kwargs = mock_task_service.update_task.call_args
    assert args[0] == "task-1"
    assert args[1]["status"] == "dispatched"
    assert args[1]["retry_count"] == 1
    assert "嘗試重新執行" in args[1]["description"]

@pytest.mark.asyncio
async def test_recover_zombie_tasks_dlq(mock_task_service):
    # Setup mock returns: one zombie task with retry_count >= 3
    mock_task_service.list_tasks.side_effect = [
        # Call 1: processing
        (True, {"tasks": []}),
        # Call 2: doing
        (True, {"tasks": [{"id": "task-2", "retry_count": 3, "description": ""}]})
    ]

    worker = WorkerService()
    await worker._recover_zombie_tasks()

    # Assert update_task was called with failed
    mock_task_service.update_task.assert_called_once()
    args, kwargs = mock_task_service.update_task.call_args
    assert args[0] == "task-2"
    assert args[1]["status"] == "failed"
    assert "放棄自動重試" in args[1]["description"]
