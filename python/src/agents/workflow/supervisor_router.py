"""Supervisor routing via Gemini Decisions API with automatic fallback to generative Supervisor model."""

import logging
from typing import Any, cast

from pydantic_ai import Agent

from src.server.config.model_ssot import get_model_path
from src.server.services.agent_registry import get_agent_config
from src.server.services.llm.decisions_client import DecisionsUnavailableError, decisions_client

from .state import SharedState, SupervisorDecision
from .utils import PAI_V1, _accumulate_usage, _get_output, _run_agent_with_retry

logger = logging.getLogger(__name__)


def build_supervisor_route_criteria(node_routing: dict[str, str], is_daily: bool) -> dict[str, str]:
    """Build closed-set choice criteria dynamically from workflow node_routing and agent_registry SSOT."""
    terminal_criteria = {
        "end": "Finish the workflow now because all required steps are complete.",
        "human": "Escalate to human review because approval or manual intervention is needed.",
    }
    criteria: dict[str, str] = {}
    for key in node_routing:
        norm = str(key).strip().lower()
        if not norm:
            continue
        cfg = get_agent_config(norm)
        if cfg:
            desc = cfg.get("description") or ""
            criteria[norm] = f"Route to {cfg['name']}: {desc}" if desc else f"Route to {cfg['name']}."
        else:
            criteria[norm] = f"Route to workflow node '{norm}'."
    criteria.setdefault("end", terminal_criteria["end"])
    if not is_daily:
        criteria.setdefault("human", terminal_criteria["human"])
    return criteria


async def route_supervisor_step(
    *,
    ctx_state: SharedState,
    model_name: str,
    system_prompt: str,
    history_text: str,
    node_routing: dict[str, str],
    agent_cls: Any = None,
    run_agent_fn: Any = None,
    get_output_fn: Any = None,
    accumulate_usage_fn: Any = None,
) -> SupervisorDecision:
    """Primary: Gemini Decisions API (`gemini-decision-1`); Fallback: generative Supervisor Agent."""
    is_daily = (ctx_state.task_type or "").lower().replace(" ", "").replace("_", "") == "dailyexecutivesummary"
    criteria = build_supervisor_route_criteria(node_routing, is_daily=is_daily)
    decision_input = f"Task Type: {ctx_state.task_type}\n\nSupervisor Policy:\n{system_prompt[:2000]}\n\nHistory:\n{history_text}"

    try:
        res = await decisions_client.classify_choice(
            input_text=decision_input,
            question_key="next_node",
            instructions="Select the single next workflow node or 'end' based on the supervisor policy and history.",
            criteria=criteria,
            context_type="supervisor_routing_decision",
        )
        ctx_state.input_tokens += res.input_tokens
        ctx_state.model_used = get_model_path("DECISION_MODEL").replace("models/", "")
        return SupervisorDecision.model_validate(
            {
                "next_node": res.choice,
                "reasoning": f"Decisions API routed to '{res.choice}' (confidence={res.confidence:.0%}).",
            }
        )
    except DecisionsUnavailableError as err:
        logger.warning(f"⚠️ [Supervisor] Decisions API unavailable, falling back to '{model_name}': {err}")

    agent_args: dict[str, Any] = {"model": model_name, "system_prompt": system_prompt}
    if PAI_V1:
        agent_args["output_type"] = SupervisorDecision
    else:
        agent_args["result_type"] = SupervisorDecision

    resolved_agent_cls = agent_cls or Agent
    resolved_run_fn = run_agent_fn or _run_agent_with_retry
    resolved_get_output = get_output_fn or _get_output
    resolved_accumulate = accumulate_usage_fn or _accumulate_usage

    router_agent = resolved_agent_cls(**agent_args)
    result = await resolved_run_fn(
        router_agent, f"History:\n{history_text}\n\nDecide next step.", ctx_state, model_name
    )
    resolved_accumulate(ctx_state, result, model_name)
    return cast(SupervisorDecision, resolved_get_output(result))
