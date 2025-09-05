import pytest
from unittest.mock import AsyncMock
from src.agents.echo_agent import EchoAgent

@pytest.mark.asyncio
async def test_echo_agent_arun_method_with_monkeypatch(monkeypatch):
    """
    Tests the EchoAgent's arun method using the monkeypatch pattern
    to mock the asynchronous method.
    """
    # 1. Arrange: Create an AsyncMock with a predefined return value.
    # This simulates the behavior of the real method.
    mock_arun = AsyncMock(return_value=(True, "mocked echo response"))

    # 2. Arrange: Use monkeypatch to replace the actual `arun` method on the EchoAgent class
    # with our mock. Any instance of EchoAgent will now use the mock.
    monkeypatch.setattr(EchoAgent, "arun", mock_arun)

    # 3. Act: Instantiate the agent and call the method we patched.
    agent = EchoAgent()
    success, result = await agent.arun("hello world")

    # 4. Assert: Verify the results and that the mock was called correctly.
    assert success is True
    assert result == "mocked echo response"
    mock_arun.assert_called_once_with("hello world")
    print("\nTest passed: EchoAgent was successfully mocked using the monkeypatch pattern.")

