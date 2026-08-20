import json
import logging
import os
from collections.abc import AsyncGenerator
from typing import cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..models import AgentInfo, AgentListResponse, AgentRequest, AgentResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents", tags=["agents"])

@router.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest, req: Request):
    try:
        if request.agent_type not in req.app.state.agents:
            raise HTTPException(status_code=400, detail=f"Unknown agent type: {request.agent_type}")

        agent = req.app.state.agents[request.agent_type]
        deps = {
            "context": request.context or {},
            "options": request.options or {},
            "mcp_endpoint": os.getenv("MCP_SERVICE_URL", "http://archon-mcp:8051"),
        }
        result = await agent.run(request.prompt, deps)

        return AgentResponse(
            success=True,
            result=result,
            metadata={"agent_type": request.agent_type, "model": agent.model},
        )
    except Exception as e:
        logger.error(f"Error running {request.agent_type} agent: {e}")
        return AgentResponse(success=False, error=str(e))

@router.get("/list", response_model=AgentListResponse)
async def list_agents(req: Request) -> AgentListResponse:
    agents_info: dict[str, AgentInfo] = {}

    for name, agent in req.app.state.agents.items():
        agents_info[name] = AgentInfo(
            name=agent.name,
            model=agent.model,
            description=agent.__class__.__doc__ or "No description available",
            available=True,
        )

    return AgentListResponse(agents=agents_info, total=len(agents_info))

@router.post("/{agent_type}/stream")
async def stream_agent(agent_type: str, request: AgentRequest, req: Request) -> StreamingResponse:
    if agent_type not in req.app.state.agents:
        raise HTTPException(status_code=400, detail=f"Unknown agent type: {agent_type}")

    agent = req.app.state.agents[agent_type]

    async def generate() -> AsyncGenerator[str, None]:
        try:
            from ..base_agent import ArchonDependencies
            deps: ArchonDependencies

            if agent_type == "rag":
                from ..rag_agent import RagDependencies
                deps = RagDependencies(
                    source_filter=request.context.get("source_filter") if request.context else None,
                    match_count=request.context.get("match_count", 5) if request.context else 5,
                    project_id=cast(str, request.context.get("project_id")) if request.context else None,
                )
            elif agent_type == "document":
                from ..document_agent import DocumentDependencies
                deps = DocumentDependencies(
                    project_id=cast(str, (request.context.get("project_id") if request.context else "") or ""),
                    user_id=cast(str, request.context.get("user_id")) if request.context else None,
                )
            elif agent_type == "presentation":
                from ..presentation.presentation_agent import PresentationDependencies
                deps = PresentationDependencies(
                    topic=cast(str, request.context.get("topic", "")),
                    notebook_id=cast(str, request.context.get("notebook_id", "")),
                    task_id=cast(str, request.context.get("task_id", "")),
                    project_id=cast(str, request.context.get("project_id", "")),
                )
            else:
                deps = ArchonDependencies()

            async with agent.run_stream(request.prompt, deps) as stream:
                async for chunk in stream.stream_text():
                    event_data = json.dumps({"type": "stream_chunk", "content": chunk})
                    yield f"data: {event_data}\n\n"

                try:
                    final_result = await stream.get_data()
                    event_data = json.dumps({"type": "stream_complete", "content": final_result})
                    yield f"data: {event_data}\n\n"
                except Exception:
                    event_data = json.dumps({"type": "stream_complete", "content": ""})
                    yield f"data: {event_data}\n\n"

        except Exception as e:
            logger.error(f"Error streaming {agent_type} agent: {e}")
            event_data = json.dumps({"type": "error", "error": str(e)})
            yield f"data: {event_data}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
