from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI

from src.agents.lifespan import lifespan


@pytest.mark.asyncio
async def test_lifespan_fail_fast():
    """Test that lifespan raises RuntimeError when credentials cannot be fetched."""
    app = FastAPI()

    # Mock fetch_credentials_from_server to simulate connection failure (Exception)
    with patch("src.agents.lifespan.fetch_credentials_from_server", side_effect=Exception("Connection refused")):
        with pytest.raises(RuntimeError) as exc_info:
            async with lifespan(app):
                pass

        assert "Fail-Fast: Cannot start Agents service without credentials." in str(exc_info.value)

@pytest.mark.asyncio
async def test_lifespan_success():
    """Test that lifespan succeeds when credentials can be fetched and models are provided."""
    app = FastAPI()

    # We mock fetch_credentials_from_server to just pass
    with patch("src.agents.lifespan.fetch_credentials_from_server", new_callable=AsyncMock):
        # Also need to mock AGENT_CREDENTIALS so the loop finds the models
        with patch.dict("src.agents.lifespan.AGENT_CREDENTIALS", {
            "DOCUMENT_AGENT_MODEL": "test-doc-model",
            "RAG_AGENT_MODEL": "test-rag-model",
            "PRESENTATION_AGENT_MODEL": "test-pres-model",
        }):
            # Mock the agent classes so they don't actually instantiate and call LLMs
            with patch("src.agents.lifespan.AVAILABLE_AGENTS", {
                "document": MagicMock(),
                "rag": MagicMock(),
                "presentation": MagicMock(),
            }):
                async with lifespan(app):
                    assert "document" in app.state.agents
                    assert "rag" in app.state.agents
                    assert "presentation" in app.state.agents
