import httpx
import asyncio
import json

BASE_URL = "http://localhost:8181/api"
USERS = {
    "David (Admin)": "admin@archon.com",
    "Alice (Sales)": "alice@archon.com",
    "Bob (Mkt)": "bob@archon.com",
    "Charlie (Mgr)": "charlie@archon.com",
    "DevBot (Agent)": "dev.bot@archon.com"
}
PW = "qwer45tyuiop"

async def test_persona(name, email):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            from src.server.utils import get_supabase_client
            sb = get_supabase_client()
            res = sb.auth.sign_in_with_password({"email": email, "password": PW})
            token = res.session.access_token
        except Exception as e:
            return f"❌ Login Failed: {str(e)}"

        headers = {"Authorization": f"Bearer {token}"}
        
        # Physical Path Alignment from Grep Reality:
        # admin -> /admin/rbac/matrix (Prefix defined in admin_api.py)
        # sales/mkt -> /marketing/leads (Prefix defined in marketing_api.py)
        # mgr -> /stats/system-overview (Prefix defined in stats_api.py)
        # agent -> /mcp/status (Prefix defined in mcp_api.py)
        
        endpoints = {
            "David (Admin)": "/admin/rbac/matrix",
            "Alice (Sales)": "/marketing/leads",
            "Bob (Mkt)": "/marketing/sources",
            "Charlie (Mgr)": "/stats/system-overview",
            "DevBot (Agent)": "/mcp/status"
        }
        
        url = BASE_URL + endpoints[name]
        resp = await client.get(url, headers=headers)
        return f"{resp.status_code} | {resp.text[:30]}..."

async def main():
    print("--- 5-Persona Final Physical Parity ---")
    for name, email in USERS.items():
        result = await test_persona(name, email)
        print(f"{name:15}: {result}")

if __name__ == "__main__":
    asyncio.run(main())
