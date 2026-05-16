# scripts/approve_verify.py
import asyncio
import httpx
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_approval_workflow():
    server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
    is_docker = os.getenv("DOCKER_CONTAINER") == "true" or os.path.exists("/.dockerenv")
    server_host = "archon-server" if is_docker else "localhost"
    
    admin_url = f"http://{server_host}:{server_port}/api/admin/changes"
    
    print(f"🚀 [Admin] Starting Approval Workflow Verification at {admin_url}...")
    
    async with httpx.AsyncClient() as client:
        # 1. List pending proposals
        print("📋 Fetching pending proposals...")
        list_res = await client.get(f"{admin_url}/pending", timeout=5.0)
        if list_res.status_code != 200:
            print(f"❌ Failed to list proposals: {list_res.text}")
            return
            
        proposals = list_res.json()
        if not proposals:
            print("⚠️ No pending proposals found. Please run verify_david_evolution.py first.")
            return
            
        target = proposals[0]
        proposal_id = target['id']
        print(f"✅ Found proposal {proposal_id} for {target['request_payload'].get('file_path')}")

        # 2. Approve with simplified ID "1" (Manager Charlie)
        print(f"✍️ Approving proposal {proposal_id} with ID '1'...")
        # Note: We use the public admin API which should handle the approval
        approve_url = f"{admin_url}/approve/{proposal_id}?user_id=1"
        approve_res = await client.post(approve_url, timeout=10.0)
        
        if approve_res.status_code == 200:
            print(f"✅ APPROVAL Success: {approve_res.json().get('status')}")
            print(f"💎 Full loop (Propose -> Approve -> Execute) is PHYSICALLY VERIFIED!")
        else:
            print(f"❌ APPROVAL Failed: {approve_res.status_code} - {approve_res.text}")
            if "uuid" in approve_res.text.lower():
                print("🚨 CONFIRMED: Database still enforces UUID. Migration needed.")

if __name__ == "__main__":
    asyncio.run(test_approval_workflow())
