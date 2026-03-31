import pytest
from fastapi.testclient import TestClient

from server.api_routes.agents_api import get_current_user
from server.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_overrides():
    """Clear overrides after each test"""
    app.dependency_overrides = {}
    yield
    app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_assignable_agents_anonymous():
    """Test that anonymous users are rejected (403/401)."""
    # No override -> uses real dependency -> fails auth
    response = client.get("/api/agents/assignable")
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_get_assignable_agents_admin():
    """Test that admin sees all agents."""

    # Override dependency to simulate logged-in admin

    app.dependency_overrides[get_current_user] = lambda: {"id": "admin-1", "role": "system_admin"}

    response = client.get("/api/agents/assignable")

    assert response.status_code == 200

    agents = response.json()

    agent_names = [a["name"] for a in agents]

    # Check for Display Names from shared_constants.py

    assert "DevBot (Engineering)" in agent_names

    assert "MarketBot (Sales)" in agent_names

    assert "Librarian (Knowledge)" in agent_names


@pytest.mark.asyncio
async def test_get_assignable_agents_sales_alice():
    """Test that Alice (Sales) ONLY sees MarketBot."""

    # Override dependency to simulate Alice

    app.dependency_overrides[get_current_user] = lambda: {"id": "alice-1", "role": "sales"}

    response = client.get("/api/agents/assignable")

    assert response.status_code == 200

    agents = response.json()

    agent_names = [a["name"] for a in agents]

    # Requirement: Alice sees MarketBot

    assert "MarketBot (Sales)" in agent_names

    # Requirement: Alice DOES NOT see DevBot or Librarian

    assert "DevBot (Engineering)" not in agent_names

    assert "Librarian (Knowledge)" not in agent_names
