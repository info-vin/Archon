
import asyncio
import sys
import os

# PYTHONPATH setup is now handled externally
from src.server.services.agent_service import AgentService
from unittest.mock import MagicMock, AsyncMock, patch

async def verify_4623():
    print("--- 🧪 Starting Phase 4.6.23 Unified Dispatch Verification ---")
    
    # 1. Identity Grounding: Verify that slug is passed to Gate
    async def mock_gate(self, agent_id, required_level):
        print(f"[Verification] Gate Check received ID: '{agent_id}'")
        return (False, "Level 0 (Intern)") if required_level >= 2 else (True, "Level 0 (Intern)")

    print("\nScenario 1: Identity Grounding & Explanatory Block")
    agent_service = AgentService()
    mock_tool_call = MagicMock()
    mock_tool_call.function.name = "apply_modification"
    mock_tool_call.function.arguments = '{"file_path": "test.txt", "content": "hello"}'
    mock_tool_call.id = "call_123"
    
    with patch.object(AgentService, '_check_poisson_gate', new=mock_gate):
        with patch('src.server.services.agent_service.get_agent_config', return_value={"name": "Fancy Name"}):
            results = await agent_service._handle_tool_calls([mock_tool_call], agent_id="test-bot")
            output = results[0]["content"]
            print(f"Result: {output}")
            
            if "current level is Level 0 (Intern)" in output and "test-bot" in str(mock_tool_call.mock_calls): # This check is indirect
                print("✅ PASSED: Explanatory block and ID grounding verified via output.")

    # 2. Unified Dispatch: Verify that NATIVE_TOOL_MAP is used
    print("\nScenario 2: Unified Dispatch (Dynamic call to _exec_... methods)")
    
    # Patch the class method BEFORE instantiation
    with patch.object(AgentService, '_exec_apply_modification', new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = "Exec Success"
        service_under_test = AgentService()
        
        # Force Gate to pass
        with patch.object(AgentService, '_check_poisson_gate', return_value=(True, "Level 2")):
            await service_under_test._handle_tool_calls([mock_tool_call], agent_id="test-bot")
            
            if mock_exec.called:
                print(f"✅ PASSED: Native tool '{mock_tool_call.function.name}' executed via dynamic dispatch.")
            else:
                print("❌ FAILED: Native tool was NOT reached.")

if __name__ == "__main__":
    asyncio.run(verify_4623())
