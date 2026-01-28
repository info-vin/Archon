
import os
from unittest.mock import AsyncMock, patch

import pytest

# Adjust import based on your project structure
from python.src.server.services.agent_service import agent_service
from python.src.server.utils.code_modifier import CodeModifier

# Test Data
BROKEN_SCRIPT = "broken_script.py"
BROKEN_CONTENT = "print 'Hello World'  # Syntax Error in Python 3"
FIXED_CONTENT = "print('Hello World')  # Fixed"

@pytest.fixture
def clean_env():
    # Setup
    if os.path.exists(BROKEN_SCRIPT):
        os.remove(BROKEN_SCRIPT)
    with open(BROKEN_SCRIPT, "w") as f:
        f.write(BROKEN_CONTENT)

    initial_branch = CodeModifier().get_current_branch()

    yield

    # Teardown
    if os.path.exists(BROKEN_SCRIPT):
        os.remove(BROKEN_SCRIPT)

    modifier = CodeModifier()
    current = modifier.get_current_branch()
    if current != initial_branch and "autosave" in current:
        modifier.revert_sandbox(initial_branch)

@pytest.mark.asyncio
async def test_agent_repair_loop_python(clean_env):
    """
    Verifies that the agent service:
    1. Detects failure of the broken script.
    2. Receives a fix from the (mocked) LLM.
    3. Creates a sandbox branch.
    4. Applies the fix.
    5. Verifies the fix by re-running.
    6. Returns success.
    """

    # Mock LLM Response
    mock_llm_response = {
        "file_path": BROKEN_SCRIPT,
        "fixed_content": FIXED_CONTENT,
        "reasoning": "Fixed Python 2 print statement to Python 3 function call."
    }

    # We need to mock _analyze_error_with_structured_output directly
    # to avoid complex mocking of the OpenAI client and config
    with patch.object(
        agent_service,
        "_analyze_error_with_structured_output",
        new_callable=AsyncMock
    ) as mock_analyze:

        mock_analyze.return_value = mock_llm_response

        # ACT
        success, message = await agent_service.run_command_with_self_healing(
            f"python3 {BROKEN_SCRIPT}",
            task_id="test-repair-1"
        )

        # ASSERT
        assert success is True
        assert "Command Succeeded after Auto-Repair" in message
        assert "Sandbox Branch" in message

        # Verify file content on disk (should be fixed)
        with open(BROKEN_SCRIPT) as f:
            content = f.read()
        assert content == FIXED_CONTENT

        # Verify we are on a sandbox branch
        current_branch = agent_service.code_modifier.get_current_branch()
        assert "autosave" in current_branch

@pytest.mark.asyncio
async def test_agent_repair_loop_typescript_simulation(clean_env):
    """
    Simulates a TypeScript fix scenario (Language Agnostic check).
    We won't actually run tsc, but we'll simulate the failure/success return codes via mocking.
    """
    TS_FILE = "broken.ts"
    mock_llm_response = {
        "file_path": TS_FILE,
        "fixed_content": "const x: string = 'hello';",
        "reasoning": "Fixed type mismatch"
    }

    # ACT: Run a command that 'fails' first, then 'succeeds'
    # We mock subprocess_shell to control the outcome
    with patch("asyncio.create_subprocess_shell") as mock_shell:
        # First call (Fail), Second call (Success)
        process_fail = AsyncMock()
        process_fail.returncode = 1
        process_fail.communicate.return_value = (b"", b"Error: Type string is not assignable to type number")

        process_success = AsyncMock()
        process_success.returncode = 0
        process_success.communicate.return_value = (b"Success", b"")

        mock_shell.side_effect = [process_fail, process_success]

        with patch.object(
            agent_service,
            "_analyze_error_with_structured_output",
            new_callable=AsyncMock
        ) as mock_analyze:
            mock_analyze.return_value = mock_llm_response

            success, message = await agent_service.run_command_with_self_healing(
                f"tsc {TS_FILE}",
                task_id="test-repair-ts"
            )

            assert success is True
            assert "Command Succeeded after Auto-Repair" in message

            # Verify CodeModifier was called to apply fix
            # (We didn't mock CodeModifier, so it likely tried to write to disk.
            # In a real test we might want to mock CodeModifier.apply_modification too if we don't want IO)
            # But let's check the branch name logic is agnostic
            assert "autosave" in message
