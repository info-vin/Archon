"""
Agents Service - Lightweight FastAPI server for PydanticAI agents

This service ONLY hosts PydanticAI agents. It does NOT contain:
- ML models or embeddings (those are in Server)
- Direct database access (use MCP tools)
- Business logic (that's in Server)

The agents use MCP tools for all data operations.
"""

import logging
import os

import uvicorn
from fastapi import FastAPI

from .lifespan import lifespan
from .rerank_router import router as rerank_router
from .routes.endpoints import router as endpoints_router
from .routes.health import router as health_router
from .routes.workflow import router as workflow_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("google_genai._api_client").setLevel(logging.ERROR)

# Create FastAPI app
app = FastAPI(
    title="Archon Agents Service",
    description="Lightweight service hosting PydanticAI agents",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(rerank_router, prefix="/ml", tags=["ml"])
app.include_router(workflow_router)
app.include_router(endpoints_router)

# Main entry point
if __name__ == "__main__":
    agents_port = os.getenv("ARCHON_AGENTS_PORT")
    if not agents_port:
        raise ValueError(
            "ARCHON_AGENTS_PORT environment variable is required. "
            "Please set it in your .env file or environment. "
            "Default value: 8052"
        )
    port = int(agents_port)

    uvicorn.run(
        "src.agents.server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False,  # Disable reload in production
    )
