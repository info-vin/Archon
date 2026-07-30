import logging

from fastapi import APIRouter

from ..models import AgentResponse, WorkflowRequest
from ..workflow_engine import WorkflowEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agents/workflow", tags=["workflow"])

@router.post("/run", response_model=AgentResponse)
async def run_workflow(request: WorkflowRequest):
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
