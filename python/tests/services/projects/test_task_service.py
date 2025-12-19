import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import asyncio

from src.server.services.projects.task_service import TaskService, AI_AGENT_ROLES

@pytest.mark.asyncio
class TestTaskServiceAIAssignment(unittest.TestCase):

    @patch('src.server.services.projects.task_service.agent_service')
    async def test_create_task_with_ai_assignee_notifies_agent_service(self, mock_agent_service):
        mock_agent_service.run_agent_task = AsyncMock()
        mock_supabase_client = MagicMock()
        task_service = TaskService(supabase_client=mock_supabase_client)
        
        ai_agent_name = list(AI_AGENT_ROLES)[0]
        task_id = "task-abc"
        mock_task_data = {"id": task_id, "assignee": ai_agent_name, "project_id": "p1", "title": "t1"}
        
        execute_mock = MagicMock()
        execute_mock.data = [mock_task_data]
        mock_supabase_client.table.return_value.insert.return_value.execute.return_value = execute_mock

        await task_service.create_task(project_id="p1", title="t1", assignee=ai_agent_name)
        await asyncio.sleep(0.01)

        mock_agent_service.run_agent_task.assert_awaited_once_with(task_id=task_id, agent_id=ai_agent_name)

    @patch('src.server.services.projects.task_service.agent_service')
    async def test_update_task_to_ai_assignee_notifies_agent_service(self, mock_agent_service):
        mock_agent_service.run_agent_task = AsyncMock()
        mock_supabase_client = MagicMock()
        task_service = TaskService(supabase_client=mock_supabase_client)

        ai_agent_name = list(AI_AGENT_ROLES)[0]
        task_id = "task-xyz"
        
        mock_current_task = {"id": task_id, "assignee": "human-user"}
        mock_updated_task = {"id": task_id, "assignee": ai_agent_name}
        
        get_execute_mock = MagicMock()
        get_execute_mock.data = [mock_current_task]
        mock_supabase_client.table.return_value.select.return_value.eq.return_value.execute.return_value = get_execute_mock

        update_execute_mock = MagicMock()
        update_execute_mock.data = [mock_updated_task]
        mock_supabase_client.table.return_value.update.return_value.eq.return_value.execute.return_value = update_execute_mock

        update_fields = {"assignee": ai_agent_name}

        await task_service.update_task(task_id, update_fields)
        await asyncio.sleep(0.01)

        mock_agent_service.run_agent_task.assert_awaited_once_with(task_id=task_id, agent_id=ai_agent_name)
