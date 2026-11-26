"""Unit tests for Gemini Decisions API client and dual-track automatic fallback (LeadEvaluator + Supervisor)."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents.workflow.state import SharedState, SupervisorDecision
from src.agents.workflow.supervisor_router import route_supervisor_step
from src.server.services.crawling.clients.job104_client import JobData
from src.server.services.crawling.lead_evaluator import LeadEvaluator
from src.server.services.llm.decisions_client import (
    DecisionChoiceResult,
    DecisionsClient,
    DecisionsUnavailableError,
)


class TestDecisionsClient:
    @pytest.mark.asyncio
    async def test_classify_choice_rotates_key_on_429_and_logs_zero_output_tokens(self):
        client = DecisionsClient(timeout_seconds=5.0)
        resp_429 = MagicMock(status_code=429, text="quota exceeded")
        resp_200 = MagicMock(
            status_code=200,
            json=lambda: {
                "answers": {"cat": {"choice": "A", "confidence": 0.91, "probabilities": {"A": 0.91, "X": 0.09}}},
                "usage": {"total_input_tokens": 140, "total_output_tokens": 0},
            },
        )
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(side_effect=[resp_429, resp_200])
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_http)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(DecisionsClient, "_get_api_keys", AsyncMock(return_value=["key-1", "key-2"])),
            patch.object(DecisionsClient, "_resolve_endpoint", return_value="https://example.test/v1beta/decisions"),
            patch("src.server.services.llm.decisions_client.httpx.AsyncClient", return_value=mock_cm),
            patch("src.server.services.token_usage_service.TokenUsageService.log_usage", AsyncMock()) as mock_log,
        ):
            res = await client.classify_choice(
                input_text="sample",
                question_key="cat",
                instructions="classify",
                criteria={"A": "enterprise", "X": "other"},
                context_type="unit_test",
            )

        assert res.choice == "A"
        assert res.confidence == pytest.approx(0.91)
        assert res.input_tokens == 140
        assert mock_http.post.call_count == 2
        mock_log.assert_awaited_once()
        assert mock_log.await_args.kwargs["output_tokens"] == 0

    @pytest.mark.asyncio
    async def test_classify_choice_raises_unavailable_on_404(self):
        client = DecisionsClient(timeout_seconds=5.0)
        resp_404 = MagicMock(status_code=404, text="not found")
        mock_http = AsyncMock()
        mock_http.post = AsyncMock(return_value=resp_404)
        mock_cm = MagicMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_http)
        mock_cm.__aexit__ = AsyncMock(return_value=False)

        with (
            patch.object(DecisionsClient, "_get_api_keys", AsyncMock(return_value=["key-1"])),
            patch.object(DecisionsClient, "_resolve_endpoint", return_value="https://example.test/v1beta/decisions"),
            patch("src.server.services.llm.decisions_client.httpx.AsyncClient", return_value=mock_cm),
            pytest.raises(DecisionsUnavailableError, match="HTTP 404"),
        ):
            await client.classify_choice(
                input_text="sample",
                question_key="cat",
                instructions="classify",
                criteria={"A": "enterprise", "X": "other"},
                context_type="unit_test",
            )


class TestDualTrackFallback:
    @pytest.mark.asyncio
    async def test_lead_evaluator_uses_decisions_api_and_falls_back_on_error(self):
        evaluator = LeadEvaluator(rate_limiter=MagicMock())
        job = JobData(title="AI Automation Engineer", company="Traditional Mfg Co", description="ERP workflow")

        with (
            patch.object(evaluator, "get_core_text", AsyncMock(return_value="Archon Core")),
            patch(
                "src.server.services.llm.decisions_client.decisions_client.classify_choice",
                AsyncMock(return_value=DecisionChoiceResult("A", 0.89, {"A": 0.89}, 120)),
            ),
        ):
            primary_res = await evaluator.evaluate_lead_structured(job)

        assert primary_res.category == "A"
        assert primary_res.confidence == pytest.approx(0.89)

        with (
            patch.object(evaluator, "get_core_text", AsyncMock(return_value="Archon Core")),
            patch(
                "src.server.services.llm.decisions_client.decisions_client.classify_choice",
                AsyncMock(side_effect=DecisionsUnavailableError("404 shutdown")),
            ),
            patch.object(
                evaluator,
                "generate_llm_response",
                AsyncMock(return_value='{"category": "C", "confidence": 0.92, "reason": "SI 同業"}'),
            ) as mock_llm,
        ):
            fallback_res = await evaluator.evaluate_lead_structured(job)

        mock_llm.assert_awaited_once()
        assert fallback_res.category == "C"
        assert fallback_res.reason == "SI 同業"

    @pytest.mark.asyncio
    async def test_supervisor_router_uses_decisions_api_and_falls_back_to_agent(self):
        state = SharedState(task_id="t1", task_type="Daily Executive Summary", messages=[])
        routing = {"marketbot": "MarketBotNode", "devbot": "DevBotNode", "summary": "SummaryNode"}

        with patch(
            "src.agents.workflow.supervisor_router.decisions_client.classify_choice",
            AsyncMock(return_value=DecisionChoiceResult("marketbot", 0.93, {"marketbot": 0.93}, 210)),
        ):
            primary_decision = await route_supervisor_step(
                ctx_state=state,
                model_name="gemini-3.6-flash",
                system_prompt="Route daily workflow.",
                history_text="start",
                node_routing=routing,
            )

        assert primary_decision.next_node == "marketbot"
        assert state.model_used == "gemini-decision-1"
        assert state.input_tokens == 210

        fake_result = SimpleNamespace(
            output=SupervisorDecision(next_node="devbot", reasoning="fallback agent"),
            usage=lambda: SimpleNamespace(request_tokens=50, response_tokens=10),
        )
        with (
            patch(
                "src.agents.workflow.supervisor_router.decisions_client.classify_choice",
                AsyncMock(side_effect=DecisionsUnavailableError("429 quota")),
            ),
            patch("src.agents.workflow.supervisor_router.Agent", return_value=MagicMock()),
            patch("src.agents.workflow.supervisor_router._run_agent_with_retry", AsyncMock(return_value=fake_result)) as mock_retry,
        ):
            fallback_decision = await route_supervisor_step(
                ctx_state=state,
                model_name="gemini-3.6-flash",
                system_prompt="Route daily workflow.",
                history_text="marketbot done",
                node_routing=routing,
            )

        mock_retry.assert_awaited_once()
        assert fallback_decision.next_node == "devbot"
        assert fallback_decision.reasoning == "fallback agent"
