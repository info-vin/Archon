import logging

from fastapi import APIRouter

from src.agents.checkpoint_manager import AgentCheckpointManager
from src.server.services.shared_constants import TaskFeatureEnum

from ..models import AgentResponse, WorkflowRequest
from ..workflow import WorkflowEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents/workflow", tags=["workflow"])


@router.post("/run", response_model=AgentResponse)
async def run_workflow(request: WorkflowRequest):
    try:
        ctx = request.context or {}
        task_type = ctx.get("task_type", TaskFeatureEnum.GENERAL.value)
        conversation_id = ctx.get("conversation_id") or ctx.get("task_id")

        engine = WorkflowEngine()
        checkpoint_mgr = AgentCheckpointManager()
        result = await engine.run_workflow(
            request.prompt,
            task_type=task_type,
            conversation_id=str(conversation_id) if conversation_id else None,
            checkpoint_mgr=checkpoint_mgr,
        )

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
