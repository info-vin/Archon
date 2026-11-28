import pytest
from fastapi.testclient import TestClient

from src.agents.nexus_oracle_agent import (
    ConsolidatedNexusState,
    LongTermTrends,
    NexusDependencies,
    NexusOracleAgent,
    ShortTermKPIs,
)
from src.server.main import app
from src.server.models.auth_models import UserProfileDTO

client = TestClient(app)


@pytest.mark.asyncio
async def test_nexus_oracle_agent_creation():
    """Verify that NexusOracleAgent can be initialized and configured."""
    agent = NexusOracleAgent()
    assert agent.name == "NexusOracleAgent"
    assert agent.model is not None
    assert agent.get_system_prompt() is not None


@pytest.mark.asyncio
async def test_nexus_oracle_agent_mock_run(monkeypatch):
    """Verify that the agent returns structured output conforming to ConsolidatedNexusState."""
    agent = NexusOracleAgent()
    deps = NexusDependencies(request_id="test-nexus-oracle-run")

    # We mock the _run_agent call since actual LLM requires live connectivity
    async def mock_run_agent(user_prompt: str, deps: NexusDependencies) -> ConsolidatedNexusState:
        return ConsolidatedNexusState(
            system_status="GREEN",
            health_score=95,
            short_term_kpis=ShortTermKPIs(
                daily_token_cost=0.05,
                active_error_counts=0,
                system_telemetry={"errors_24h": 0, "cost_24h": 0.05, "active_agents": [], "rag": {}, "knowledge_stats": {}},
                team_readiness={"score": 100},
                pending_approvals=[],
                active_alerts=[]
            ),
            long_term_trends=LongTermTrends(
                monthly_budget_forecast="Under budget forecast: $1.50",
                roi_trend="Positive ROI: 4.5",
                efficiency_trend="System efficiency optimal at 99.8%",
                ai_token_usage_30d={},
                knowledge_base_roi={},
                collaboration_synergy={},
                sla_reliability={},
                commander_trends=[],
                business_risks=[]
            ),
            main_bottleneck="None - All systems optimal",
            recommended_actions=[]
        )

    monkeypatch.setattr(agent, "_run_agent", mock_run_agent)

    result = await agent.run(
        user_prompt="Analyze metrics",
        deps=deps
    )

    assert isinstance(result, ConsolidatedNexusState)
    assert result.system_status == "GREEN"
    assert result.health_score == 95
    assert result.short_term_kpis.daily_token_cost == 0.05
    assert result.long_term_trends.roi_trend == "Positive ROI: 4.5"
    assert len(result.recommended_actions) == 0


def test_consolidated_api_endpoint(monkeypatch):
    """Verify that the GET /api/stats/consolidated endpoint functions and returns stats."""
    # Mock the agent run on route execution
    from src.agents.nexus_oracle_agent import NexusOracleAgent

    async def mock_agent_run(self, user_prompt, deps):
        return ConsolidatedNexusState(
            system_status="GREEN",
            health_score=98,
            short_term_kpis=ShortTermKPIs(
                daily_token_cost=0.0,
                active_error_counts=0,
                system_telemetry={},
                team_readiness={},
                pending_approvals=[],
                active_alerts=[]
            ),
            long_term_trends=LongTermTrends(
                monthly_budget_forecast="Good",
                roi_trend="5.0",
                efficiency_trend="Stable",
                ai_token_usage_30d={},
                knowledge_base_roi={},
                collaboration_synergy={},
                sla_reliability={},
                commander_trends=[],
                business_risks=[]
            ),
            main_bottleneck="None",
            recommended_actions=[]
        )

    monkeypatch.setattr(NexusOracleAgent, "run", mock_agent_run)

    # Use FastAPI dependency overrides for authentication bypass
    from src.server.auth.dependencies import get_current_user

    async def mock_get_current_user():
        return UserProfileDTO(id="test-user-id", role="admin", email="test@example.com")

    app.dependency_overrides[get_current_user] = mock_get_current_user

    try:
        response = client.get(
            "/api/stats/consolidated",
            headers={"Authorization": "Bearer fake-token"}
        )
        assert response.status_code == 200
        json_data = response.json()
        assert json_data["system_status"] == "GREEN"
        assert json_data["health_score"] == 98
        assert json_data["short_term_kpis"]["daily_token_cost"] == 0.0
        assert json_data["long_term_trends"]["roi_trend"] == "5.0"
    finally:
        # Clear dependency override
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_build_db_fallback_state_uses_real_telemetry(monkeypatch):
    """Verify DB fallback maps integrity_score, errors_24h, cost_24h, pending blogs, and alerts without 85 hardcode."""
    from unittest.mock import MagicMock

    from src.server.services.stats import consolidated_service

    class FakeStatsService:
        def __init__(self):
            self.supabase = MagicMock()

        async def get_system_health_overview(self):
            return {
                "status": "healthy",
                "integrity_score": 100.0,
                "errors_24h": 0,
                "cost_24h": 0.0046,
                "knowledge_stats": {"total_sources": 21, "total_nodes": 21},
            }

        async def get_force_readiness(self):
            return {"score": 100}

        async def get_detailed_ai_usage(self, days: int = 30):
            return {"total_monthly_usd": 0.12, "budget_limit": 1.07}

        async def get_knowledge_roi(self):
            return {"overall_conversion": 0.0}

        async def get_collab_synergy(self):
            return {"snapshot": {"momentum_pct": 328.0, "total_7d": 5}}

        async def get_sla_reliability(self):
            return {"current_sla": 100.0}

        async def get_commander_trends(self):
            return []

        async def get_business_risks(self):
            return []

        async def execute_query_async(self, _query, context: str):
            if "blog" in context:
                return True, {"data": [{"id": "b1", "title": "Draft 1", "status": "draft", "created_at": "2026-11-28"}]}
            return True, {"data": [{"id": "a1", "level": "WARNING", "source": "Sentinel", "message": "Check", "created_at": "2026-11-28"}]}

    monkeypatch.setattr(consolidated_service, "StatsService", FakeStatsService)
    state = await consolidated_service._build_db_fallback_state()

    assert state["health_score"] == 100
    assert state["system_status"] == "GREEN"
    assert state["short_term_kpis"]["daily_token_cost"] == 0.0046
    assert state["short_term_kpis"]["active_error_counts"] == 0
    assert len(state["short_term_kpis"]["pending_approvals"]) == 1
    assert len(state["short_term_kpis"]["active_alerts"]) == 1


@pytest.mark.asyncio
async def test_detailed_ai_usage_reads_budget_config_ssot(monkeypatch):
    """Verify SystemMetrics.get_detailed_ai_usage reads BudgetConfig SSOT and real tokens instead of hardcoded 100.0."""
    from unittest.mock import MagicMock

    from src.server.services import settings_service, token_usage_service
    from src.server.services.stats.domains.system_metrics import SystemMetrics

    async def mock_get_daily_cost(days: int = 30):
        return [{"date": "2026-11-28", "cost": 0.5, "tokens": 2500, "request_count": 2, "models": ["gemini"]}]

    class FakeSettingsService:
        def __init__(self, _client):
            pass

        def get_all_settings(self):
            return {"WEEKLY_BUDGET_THRESHOLD": 0.7}

    monkeypatch.setattr(token_usage_service.TokenUsageService, "get_daily_cost", staticmethod(mock_get_daily_cost))
    monkeypatch.setattr(settings_service, "SettingsService", FakeSettingsService)

    metrics = SystemMetrics(supabase_client=MagicMock())
    res = await metrics.get_detailed_ai_usage(days=30)

    assert res["budget_limit"] == 3.0  # 0.7 * (30 / 7) = 3.0
    assert res["total_monthly_tokens"] == 2500
    assert res["total_monthly_usd"] == 0.5
    assert res["usage_percentage"] == 16.7  # 0.5 / 3.0 * 100

