# scripts/verify_david_evolution.py
import asyncio
import httpx
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_david_evolution():
    server_port = os.getenv("ARCHON_SERVER_PORT", "8181")
    is_docker = os.getenv("DOCKER_CONTAINER") == "true" or os.path.exists("/.dockerenv")
    server_host = "archon-server" if is_docker else "localhost"
    
    base_url = f"http://{server_host}:{server_port}/internal/david"
    
    print(f"🚀 [David] Starting Evolution Verification at {base_url}...")
    
    async with httpx.AsyncClient() as client:
        # 1. Test Read
        print("🔍 Testing David's READ capability...")
        read_res = await client.get(f"{base_url}/read?path=python/src/server/main.py", timeout=5.0)
        if read_res.status_code == 200:
            print(f"✅ READ Success: Read {len(read_res.text)} characters from main.py")
        else:
            print(f"❌ READ Failed: {read_res.status_code} - {read_res.text}")
            return

        # 2. Test Propose
        print("💡 Testing David's PROPOSE capability...")
        payload = {
            "file_path": "python/scratch/david_test.txt",
            "new_content": "David was here at 123456789",
            "summary": "David's sanity check proposal"
        }
        propose_res = await client.post(f"{base_url}/propose", json=payload, timeout=5.0)
        if propose_res.status_code == 200:
            data = propose_res.json()
            print(f"✅ PROPOSE Success: Created proposal ID {data.get('id')}")
            print(f"💎 David's evolution is PHYSICALLY VERIFIED!")
        else:
            print(f"❌ PROPOSE Failed: {propose_res.status_code} - {propose_res.text}")

if __name__ == "__main__":
    asyncio.run(test_david_evolution())
