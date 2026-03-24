import httpx
import asyncio
import sys

async def run_probe():
    # Alice 的固定身分 (來自 seed_agent_profiles.sql)
    alice_email = "alice@archon.com"
    print(f"🔍 [Probe A2] Authenticating as Alice ({alice_email})...")
    
    base_url = "http://localhost:8181"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Step 1: 取得 Dev Token (模擬登入)
        login_resp = await client.post(f"{base_url}/api/auth/dev-token", json={"email": alice_email})
        if login_resp.status_code != 200:
            print(f"🔴 [Probe A2] Auth Failed: {login_resp.text}")
            sys.exit(1)
        
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ [Probe A2] Alice Token Acquired.")
        
        # Step 2: 強行存取 Admin API (越權嘗試)
        print("\n🚀 [Probe A2] Attempting UNAUTHORIZED access to /api/admin/users...")
        admin_resp = await client.get(f"{base_url}/api/admin/users", headers=headers)
        
        print(f"📊 [Probe A2] Backend Response Status: {admin_resp.status_code}")
        
        if admin_resp.status_code == 403:
            print("💎 [Probe A2] PHYSICAL REALIZATION SUCCESS: Backend BLOCKED unauthorized access.")
            sys.exit(0)
        elif admin_resp.status_code == 200:
            print("🔴 [Probe A2] SECURITY FAILURE: Alice can see Admin data!")
            sys.exit(1)
        else:
            print(f"⚠️ [Probe A2] Unexpected Status: {admin_resp.status_code}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_probe())
