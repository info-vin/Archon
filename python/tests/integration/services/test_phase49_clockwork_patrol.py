from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from server.services.scheduler_service import scheduler_service

@pytest.mark.asyncio
async def test_run_log_patrol_creates_task():
    """
    Test that Clockwork creates a task when errors are found.
    """
    mock_supabase = MagicMock()
    
    # 1. Mock finding logs
    mock_logs = [{"id": "log-1", "source": "api", "message": "500 Error", "level": "ERROR"}]
    mock_supabase.table().select().eq().gt().limit().execute.return_value.data = mock_logs
    
    # 2. Mock finding project
    mock_supabase.table().select().limit().execute.return_value.data = [{"id": "proj-1"}]

    mock_task_service = AsyncMock()
    mock_task_service.create_task.return_value = (True, {"id": "task-repair-1"})
    
    mock_agent_service = AsyncMock()

    with patch("server.utils.get_supabase_client", return_value=mock_supabase), \
         patch("server.services.projects.task_service.task_service", mock_task_service), \
         patch("server.services.agent_service.agent_service", mock_agent_service):
         
        # Execute
        await scheduler_service._run_log_patrol()
        
        # Verify
        mock_task_service.create_task.assert_called_once()
        _, kwargs = mock_task_service.create_task.call_args
        assert kwargs["title"].startswith("Auto-Repair")
        assert "500 Error" in kwargs["description"]
        
        mock_agent_service.run_agent_task.assert_called_once()
        assert mock_agent_service.run_agent_task.call_args[0][0] == "task-repair-1"

@pytest.mark.asyncio
async def test_run_log_patrol_no_errors():
    """
    Test that Clockwork does nothing if no errors found.
    """
    mock_supabase = MagicMock()
    # Mock NO logs
    mock_supabase.table().select().eq().gt().limit().execute.return_value.data = []

    mock_task_service = AsyncMock()
    
    with patch("server.utils.get_supabase_client", return_value=mock_supabase), \
         patch("server.services.projects.task_service.task_service", mock_task_service):
         
        await scheduler_service._run_log_patrol()
        
        mock_task_service.create_task.assert_not_called()