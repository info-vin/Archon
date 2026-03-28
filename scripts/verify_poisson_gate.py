
import asyncio
import sys
import os

# PYTHONPATH setup is handled externally
from src.server.services.agent_service import AgentService
from unittest.mock import MagicMock, AsyncMock, patch

async def verify_grounded_reasoning():
    print("--- 🧪 Starting Phase 4.6.22 Grounded Reasoning Verification ---")
    
    agent_service = AgentService()
    
    async def mock_gate(self, agent_id, required_level):
        print(f"[Verification] Gate Check: {agent_id} requesting L{required_level}")
        return False if required_level >= 2 else True

    # Scenario 1: XP 0 attempts Level 2 tool
    print(f"\nScenario 1: Agent attempts Level 2 tool (apply_modification)")
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "apply_modification"
    mock_tool_call.function.arguments = '{"file_path": "test.txt", "content": "hello"}'
    mock_tool_call.id = "call_123"
    
    with patch.object(AgentService, '_check_poisson_gate', new=mock_gate):
        with patch('src.server.services.agent_service.get_agent_config', return_value={"name": "TestBot"}):
            results = await agent_service._handle_tool_calls([mock_tool_call], agent_id="test-bot")
            output = results[0]["content"]
            print(f"Result: {output}")
            if "Poisson Security Block" in output:
                print("✅ PASSED: Level 2 tool correctly blocked.")
            else:
                print("❌ FAILED: Security breach.")

    # Scenario 2: Context Packaging Verification
    print(f"\nScenario 2: Verification of Context Packaging (Reasoning)")
    
    # We patch the task_service at the module level where it's imported in agent_service.py
    # Note: agent_service.py does 'from ..services.projects.task_service import task_service'
    with patch('src.server.services.projects.task_service.TaskService.get_task', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = (True, {"task": {"title": "Fix Bug", "description": "Please run make lint-be", "id": "00000000-0000-0000-0000-000000000001"}})
        
        mock_llm_client = MagicMock()
        mock_llm_client.chat.completions.create = AsyncMock()
        mock_llm_client.__aenter__ = AsyncMock(return_value=mock_llm_client)
        mock_llm_client.__aexit__ = AsyncMock()
        
        with patch('src.server.services.agent_service.get_llm_client', return_value=mock_llm_client):
            with patch('src.server.services.agent_service.get_agent_config', return_value={"name": "DevBot", "system_prompt": "You are a dev", "tools": ["execute_shell_command"]}):
                # We need to mock update_task and save_agent_output too
                with patch('src.server.services.projects.task_service.TaskService.update_task', new_callable=AsyncMock) as mock_update:
                    with patch('src.server.services.projects.task_service.TaskService.save_agent_output', new_callable=AsyncMock):
                        try:
                            await agent_service._run_general_agent_task("00000000-0000-0000-0000-000000000001", "dev-bot")
                        except Exception as e:
                            print(f"Caught expected partial failure (or unexpected): {e}")
                        
                        if mock_llm_client.chat.completions.create.called:
                            _, kwargs = mock_llm_client.chat.completions.create.call_args
                            messages = kwargs['messages']
                            user_msg = messages[1]['content']
                            print(f"Context Sent to LLM:\n{user_msg}")
                            
                            if "Details: Please run make lint-be" in user_msg:
                                print("✅ PASSED: Instructions correctly grounded in task description.")
                            else:
                                print("❌ FAILED: Description missing from LLM context.")
                        else:
                            print("❌ FAILED: LLM client was not called.")

if __name__ == "__main__":
    asyncio.run(verify_grounded_reasoning())
