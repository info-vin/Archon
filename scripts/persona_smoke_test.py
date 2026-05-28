import httpx
import asyncio
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "http://localhost:8181/api"

# Human Personas (Phase 4.6.47 Grounded)
HUMANS = {
    "David Howard (Admin)": "admin@archon.com",
    "Alice Johnson (Sales)": "alice@archon.com",
    "Bob Williams (Mkt)": "bob@archon.com",
    "Charlie Brown (Mgr)": "charlie@archon.com",
}

# AI Agents (Physical Reality from DB/shared_constants)
AGENTS = {
    "Archon DevBot": "dev.bot@archon.com",
    "Archon MarketBot": "market.bot@archon.com",
    "Archon Librarian": "lib.bot@archon.com",
    "Archon POBot": "po.bot@archon.com",
    "Archon Clockwork": "ops.bot@archon.com",
}

PW = "qwer45tyuiop"

async def test_identity(name, email, endpoint):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            from src.server.utils import get_supabase_client
            sb = get_supabase_client()
            res = sb.auth.sign_in_with_password({"email": email, "password": PW})
            token = res.session.access_token
        except Exception as e:
            return f"❌ Login Failed: {str(e)}"

        headers = {"Authorization": f"Bearer {token}"}
        url = BASE_URL + endpoint
        try:
            resp = await client.get(url, headers=headers)
            return f"{resp.status_code} | {resp.text[:35]}..."
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ Request Failed: {str(e)}"

async def main():
    print("=== [PERSONA AUDIT 2.0] GLOBAL PHYSICAL PARITY ===")
    success = True
    
    print("\n--- 1. Human Personas (HUD Access) ---")
    human_endpoints = {
        "David Howard (Admin)": "/admin/rbac/matrix",
        "Alice Johnson (Sales)": "/marketing/leads",
        "Bob Williams (Mkt)": "/marketing/sources",
        "Charlie Brown (Mgr)": "/stats/system-overview",
    }
    for name, email in HUMANS.items():
        result = await test_identity(name, email, human_endpoints[name])
        print(f"{name:25}: {result}")
        if "❌" in result:
            success = False

    print("\n--- 2. AI Agents (Capability Access) ---")
    # All agents verify their capability via MCP status or respective service endpoints
    for name, email in AGENTS.items():
        result = await test_identity(name, email, "/mcp/status")
        print(f"{name:25}: {result}")
        if "❌" in result:
            success = False

    print("\n=== AUDIT COMPLETE ===")
    if not success:
        print("🚨 [FAILURE] Some persona checks failed!")
        exit(1)
    else:
        print("✅ [SUCCESS] All persona checks passed.")

if __name__ == "__main__":
    asyncio.run(main())

