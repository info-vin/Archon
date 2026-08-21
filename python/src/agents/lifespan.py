import asyncio
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import cast

import httpx
from fastapi import FastAPI

from .document_agent import DocumentAgent
from .rag_agent import RagAgent
from .presentation.presentation_agent import PresentationAgent

logger = logging.getLogger(__name__)

AVAILABLE_AGENTS = {
    "document": DocumentAgent,
    "rag": RagAgent,
    "presentation": PresentationAgent,
}

AGENT_CREDENTIALS: dict[str, str] = {}

async def fetch_credentials_from_server() -> dict[str, str]:
    max_retries = 30
    retry_delay = 10

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                server_port = os.getenv("ARCHON_SERVER_PORT")
                if not server_port:
                    raise ValueError(
                        "ARCHON_SERVER_PORT environment variable is required. "
                        "Please set it in your .env file or environment."
                    )
                server_host = os.getenv("ARCHON_SERVER_HOST") or os.getenv("ARCHON_HOST") or "127.0.0.1"
                response = await client.get(
                    f"http://{server_host}:{server_port}/internal/credentials/agents", timeout=10.0
                )
                response.raise_for_status()
                credentials = cast(dict[str, str], response.json())

                for key, value in credentials.items():
                    if value is not None:
                        os.environ[key] = str(value)
                        logger.info(f"Set credential: {key}")

                global AGENT_CREDENTIALS
                AGENT_CREDENTIALS = credentials

                logger.info(f"Successfully fetched {len(credentials)} credentials from server")
                return credentials

        except (httpx.HTTPError, httpx.RequestError) as e:
            if attempt < max_retries - 1:
                logger.warning(f"Failed to fetch credentials (attempt {attempt + 1}/{max_retries}): {e}")
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"Failed to fetch credentials after {max_retries} attempts")
                raise Exception("Could not fetch credentials from server") from e

    return {}

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting Agents service...")
    try:
        await fetch_credentials_from_server()
    except Exception as e:
        logger.error(f"Failed to fetch credentials: {e}")

    app.state.agents = {}
    for name, agent_class in AVAILABLE_AGENTS.items():
        try:
            model_key = f"{name.upper()}_AGENT_MODEL"
            model = AGENT_CREDENTIALS.get(model_key) or os.getenv(model_key)

            if not model:
                raise ValueError(f"❌ [SSOT Violation] Model configuration '{model_key}' missing from DB and ENV.")

            app.state.agents[name] = agent_class(model=model)
            logger.info(f"Initialized {name} agent with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize {name} agent: {e}")

    yield

    logger.info("Shutting down Agents service...")
