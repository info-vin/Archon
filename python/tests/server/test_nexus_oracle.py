import pytest
from src.agents.nexus_oracle_agent import NexusOracleAgent, NexusDependencies, ConsolidatedNexusState
from fastapi.testclient import TestClient
from src.server.main import app

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
            short_term_kpis={
                "daily_token_cost": 0.05,
                "active_errors": 0,
                "alerts_count": 0
            },
            long_term_trends={
                "monthly_forecast_usd": 1.50,
                "roi_index": 4.5,
                "sla_percentage": 99.8
            },
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
    assert "daily_token_cost" in result.short_term_kpis
    assert result.long_term_trends["roi_index"] == 4.5
    assert len(result.recommended_actions) == 0


def test_consolidated_api_endpoint(monkeypatch):
    """Verify that the GET /api/stats/consolidated endpoint functions and returns stats."""
    # Mock the agent run on route execution
    from src.agents.nexus_oracle_agent import NexusOracleAgent
    
    async def mock_agent_run(self, user_prompt, deps):
        return ConsolidatedNexusState(
            system_status="GREEN",
            health_score=98,
            short_term_kpis={"errors": 0},
            long_term_trends={"roi": 5.0},
            main_bottleneck="None",
            recommended_actions=[]
        )
        
    monkeypatch.setattr(NexusOracleAgent, "run", mock_agent_run)
    
    # Use FastAPI dependency overrides for authentication bypass
    from src.server.auth.dependencies import get_current_user
    
    async def mock_get_current_user():
        return {"id": "test-user-id", "email": "test@example.com", "role": "admin"}
        
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
        assert json_data["short_term_kpis"] == {"errors": 0}
        assert json_data["long_term_trends"] == {"roi": 5.0}
    finally:
        # Clear dependency override
        app.dependency_overrides.pop(get_current_user, None)

