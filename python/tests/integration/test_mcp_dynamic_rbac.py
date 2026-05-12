import pytest
from httpx import AsyncClient


# Skip tests if MCP server is not running
async def is_server_running():
    try:
        async with AsyncClient() as client:
            resp = await client.get("http://localhost:8051/sessions", timeout=2.0)
            return resp.status_code == 200
    except Exception:
        return False

@pytest.mark.asyncio
async def test_mcp_dynamic_rbac_list_tools():
    """
    Test that list_tools dynamically crops the tool schema based on X-Agent-Type.
    """
    if not await is_server_running():
        pytest.skip("MCP server not running on localhost:8051")

    mcp_server_url = "http://localhost:8051"
    async with AsyncClient() as client:
        # Test 1: Admin should get all tools
        resp_admin = await client.post(
            f"{mcp_server_url}/rpc",
            json={"jsonrpc": "2.0", "method": "list_tools", "params": {}, "id": 1},
            headers={"X-Agent-Type": "admin", "Content-Type": "application/json"}
        )
        assert resp_admin.status_code == 200
        admin_data = resp_admin.json()
        admin_tools = [t["function"]["name"] for t in admin_data.get("result", [])]

        # Test 2: MarketBot should have restricted tools
        resp_market = await client.post(
            f"{mcp_server_url}/rpc",
            json={"jsonrpc": "2.0", "method": "list_tools", "params": {}, "id": 2},
            headers={"X-Agent-Type": "marketbot", "Content-Type": "application/json"}
        )
        assert resp_market.status_code == 200
        market_data = resp_market.json()
        market_tools = [t["function"]["name"] for t in market_data.get("result", [])]

        # Assert RBAC Cropping
        if "manage_project" in admin_tools:
            assert "manage_project" not in market_tools
            assert len(admin_tools) > len(market_tools)

@pytest.mark.asyncio
async def test_mcp_dynamic_rbac_tool_execution_enforcement():
    """
    Test that calling a restricted tool directly is blocked by execution enforcement.
    """
    if not await is_server_running():
        pytest.skip("MCP server not running on localhost:8051")

    mcp_server_url = "http://localhost:8051"
    async with AsyncClient() as client:
        # MarketBot tries to call manage_project
        resp_market = await client.post(
            f"{mcp_server_url}/rpc",
            json={
                "jsonrpc": "2.0",
                "method": "manage_project",
                "params": {"action": "create", "title": "Hacked Project"},
                "id": 3
            },
            headers={"X-Agent-Type": "marketbot", "Content-Type": "application/json"}
        )

        # Expecting our 403 Forbidden RBAC violation
        assert resp_market.status_code == 403
        error_data = resp_market.json()
        assert error_data.get("error", {}).get("code") == -32003
        assert "RBAC Violation" in error_data.get("error", {}).get("message", "")
