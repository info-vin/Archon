
import openai
import pytest
from google import genai
from pydantic_ai import Agent

from src.server.config.model_ssot import SYSTEM_MODELS


@pytest.mark.asyncio
async def test_genai_client_is_mocked():
    """Verify that google.genai.Client generates mocked content locally without internet."""
    client = genai.Client(api_key="fake-test-key")
    response = client.models.generate_content(model=SYSTEM_MODELS["DEFAULT_TEXT"], contents="Hello")
    assert "Mocked GenAI Response" in response.text

    # Verify async
    response_async = await client.aio.models.generate_content(model=SYSTEM_MODELS["DEFAULT_TEXT"], contents="Hello")
    assert "Mocked GenAI Response" in response_async.text


@pytest.mark.asyncio
async def test_openai_client_is_mocked():
    """Verify that openai.OpenAI / AsyncOpenAI returns mocked completions."""
    client = openai.OpenAI(api_key="fake-test-key")
    resp = client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": "hi"}])
    assert "Mocked OpenAI Response" in resp.choices[0].message.content

    client_async = openai.AsyncOpenAI(api_key="fake-test-key")
    resp_async = await client_async.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": "hi"}])
    assert "Mocked OpenAI Response" in resp_async.choices[0].message.content


@pytest.mark.asyncio
async def test_pydantic_ai_agent_is_mocked():
    """Verify that pydantic_ai.Agent.run utilizes global mock result."""
    pydantic_model = f"google-gla:{SYSTEM_MODELS['DEFAULT_TEXT'].replace('models/', '')}"
    agent = Agent(pydantic_model, system_prompt="Test system prompt")
    result = await agent.run("test user prompt")
    assert result.data == "Mocked Agent Response"
    assert result.output == "Mocked Agent Response"
    assert result.usage.input_tokens == 10
    assert result.usage.output_tokens == 10

@pytest.mark.integration
def test_integration_auto_skip_check():
    """This integration test should run only if keys and internet are available.
    Otherwise it will be skipped by pytest_runtest_setup.
    """
    assert True
