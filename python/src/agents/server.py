"""
Agents Service - Lightweight FastAPI server for PydanticAI agents

This service ONLY hosts PydanticAI agents. It does NOT contain:
- ML models or embeddings (those are in Server)
- Direct database access (use MCP tools)
- Business logic (that's in Server)

The agents use MCP tools for all data operations.
"""

import asyncio
import json
import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, cast

import httpx
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import our PydanticAI agents
from .document_agent import DocumentAgent
from .rag_agent import RagAgent
from .rerank_router import router as rerank_router
from .workflow_engine import WorkflowEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logging.getLogger("google_genai._api_client").setLevel(logging.ERROR)


# Request/Response models
class AgentRequest(BaseModel):
    """Request model for agent interactions"""

    agent_type: str  # "document", "rag", etc.
    prompt: str
    context: dict[str, Any] | None = None
    options: dict[str, Any] | None = None


class AgentResponse(BaseModel):
    """Response model for agent interactions"""

    success: bool
    result: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


# Agent registry
AVAILABLE_AGENTS = {
    "document": DocumentAgent,
    "rag": RagAgent,
}

# Global credentials storage
AGENT_CREDENTIALS: dict[str, str] = {}


async def fetch_credentials_from_server() -> dict[str, str]:
    """Fetch credentials from the server's internal API."""
    max_retries = 30  # Try for up to 5 minutes (30 * 10 seconds)
    retry_delay = 10  # seconds

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                # Call the server's internal credentials endpoint
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

                # Set credentials as environment variables
                for key, value in credentials.items():
                    if value is not None:
                        os.environ[key] = str(value)
                        logger.info(f"Set credential: {key}")

                # Store credentials globally for agent initialization
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


# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and cleanup resources"""
    logger.info("Starting Agents service...")

    # Fetch credentials from server first
    try:
        await fetch_credentials_from_server()
    except Exception as e:
        logger.error(f"Failed to fetch credentials: {e}")
        # Continue with defaults if we can't get credentials

    # Initialize agents with fetched credentials
    app.state.agents = {}
    for name, agent_class in AVAILABLE_AGENTS.items():
        try:
            # Pass model configuration from credentials, fallback to ENV
            model_key = f"{name.upper()}_AGENT_MODEL"
            model = AGENT_CREDENTIALS.get(model_key) or os.getenv(model_key)

            if not model:
                raise ValueError(f"❌ [SSOT Violation] Model configuration '{model_key}' missing from DB and ENV.")

            app.state.agents[name] = agent_class(model=model)
            logger.info(f"Initialized {name} agent with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize {name} agent: {e}")

    yield

    # Cleanup
    logger.info("Shutting down Agents service...")


# Create FastAPI app
app = FastAPI(
    title="Archon Agents Service",
    description="Lightweight service hosting PydanticAI agents",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(rerank_router, prefix="/ml", tags=["ml"])


# --- Workflow Endpoint (Phase 5.2) ---
class WorkflowRequest(BaseModel):
    prompt: str
    context: dict[str, Any] | None = None


@app.post("/agents/workflow/run", response_model=AgentResponse)
async def run_workflow(request: WorkflowRequest):
    """
    Run a multi-agent workflow using the pydantic-graph State Router.
    Phase 5.2: Supervisor / Worker Topology.
    Phase 5.0.2: Pass context for Dynamic Prompt Governance.
    """
    try:
        task_type = "General"
        if request.context:
            task_type = request.context.get("task_type", "General")

        engine = WorkflowEngine()
        result = await engine.run_workflow(request.prompt, task_type)

        if result["success"]:
            return AgentResponse(
                success=True,
                result=result["final_result"],
                metadata={"step_count": result["step_count"], "messages": result["messages"]},
            )
        else:
            return AgentResponse(
                success=False,
                error=result.get("error", "Unknown error in workflow"),
                metadata={"step_count": result["step_count"]},
            )
    except Exception as e:
        logger.error(f"Error in workflow endpoint: {e}")
        return AgentResponse(success=False, error=str(e))


class RootResponse(BaseModel):
    status: str
    service: str

@app.get("/", response_model=RootResponse)
@app.head("/", response_model=RootResponse)
async def root() -> RootResponse:
    """Root endpoint for the agents service"""
    return RootResponse(status="healthy", service="agents")


class HealthResponse(BaseModel):
    status: str
    service: str
    agents_available: list[str]
    note: str

@app.get("/health", response_model=HealthResponse)
@app.head("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="agents",
        agents_available=list(AVAILABLE_AGENTS.keys()),
        note="This service only hosts PydanticAI agents",
    )


@app.post("/agents/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """
    Run a specific agent with the given prompt.

    The agent will use MCP tools for any data operations.
    """
    try:
        # Get the requested agent
        if request.agent_type not in app.state.agents:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")

        agent = app.state.agents[request.agent_type]

        # Prepare dependencies for the agent
        deps = {
            "context": request.context or {},
            "options": request.options or {},
            "mcp_endpoint": os.getenv("MCP_SERVICE_URL", "http://archon-mcp:8051"),
        }

        # Run the agent
        result = await agent.run(request.prompt, deps)

        return AgentResponse(
            success=True,
            result=result,
            metadata={"agent_type": request.agent_type, "model": agent.model},
        )

    except Exception as e:
        logger.error(f"Error running {request.agent_type} agent: {e}")
        return AgentResponse(success=False, error=str(e))


class AgentInfo(BaseModel):
    name: str
    model: str
    description: str
    available: bool

class AgentListResponse(BaseModel):
    agents: dict[str, AgentInfo]
    total: int

@app.get("/agents/list", response_model=AgentListResponse)
async def list_agents() -> AgentListResponse:
    """List all available agents and their capabilities"""
    agents_info: dict[str, AgentInfo] = {}

    for name, agent in app.state.agents.items():
        agents_info[name] = AgentInfo(
            name=agent.name,
            model=agent.model,
            description=agent.__class__.__doc__ or "No description available",
            available=True,
        )

    return AgentListResponse(agents=agents_info, total=len(agents_info))


@app.post("/agents/{agent_type}/stream")
async def stream_agent(agent_type: str, request: AgentRequest) -> StreamingResponse:
    """
    Stream responses from an agent using Server-Sent Events (SSE).

    This endpoint streams the agent's response in real-time, allowing
    for a more interactive experience.
    """
    # Get the requested agent
    if agent_type not in app.state.agents:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")

    agent = app.state.agents[agent_type]

    async def generate() -> AsyncGenerator[str, None]:
        try:
            # Prepare dependencies based on agent type
            # Import dependency classes
            from .base_agent import ArchonDependencies

            deps: ArchonDependencies

            if agent_type == "rag":
                from .rag_agent import RagDependencies

                deps = RagDependencies(
                    source_filter=request.context.get("source_filter") if request.context else None,
                    match_count=request.context.get("match_count", 5) if request.context else 5,
                    project_id=cast(str, request.context.get("project_id")) if request.context else None,
                )
            elif agent_type == "document":
                from .document_agent import DocumentDependencies

                deps = DocumentDependencies(
                    project_id=cast(str, (request.context.get("project_id") if request.context else "") or ""),
                    user_id=cast(str, request.context.get("user_id")) if request.context else None,
                )
            else:
                # Default dependencies
                deps = ArchonDependencies()

            # Use PydanticAI's run_stream method
            # run_stream returns an async context manager directly
            async with agent.run_stream(request.prompt, deps) as stream:
                # Stream text chunks as they arrive
                async for chunk in stream.stream_text():
                    event_data = json.dumps({"type": "stream_chunk", "content": chunk})
                    yield f"data: {event_data}\n\n"

                # Get the final structured result
                try:
                    final_result = await stream.get_data()
                    event_data = json.dumps({"type": "stream_complete", "content": final_result})
                    yield f"data: {event_data}\n\n"
                except Exception:
                    # If we can't get structured data, just send completion
                    event_data = json.dumps({"type": "stream_complete", "content": ""})
                    yield f"data: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Error streaming {agent_type} agent: {e}")
            event_data = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {event_data}\n\n"

    # Return SSE response
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering
        },
    )


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
        "server:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        reload=False,  # Disable reload in production
    )
