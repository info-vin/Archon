import asyncio
import os
import sys
import random
from dotenv import load_dotenv

# Ensure python folder is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

for p in [".env", "python/.env", "../.env", "../python/.env"]:
    if os.path.exists(p):
        load_dotenv(p)

from src.server.utils import get_supabase_client

async def run_setup(level_id: str, force_clean: bool = True):
    print(f"🧪 [Sandbox] Initializing state for level: {level_id} (force_clean={force_clean})")
    
    # Jitter to avoid concurrent DB lockup
    await asyncio.sleep(random.uniform(0.1, 0.5))
    
    supabase = get_supabase_client()
    
    # Branching sandbox setup by level_id
    if "L1_STAGE_04" in level_id:
        print(f"🧪 [Sandbox] Routing L1_STAGE_04 to scripts.setup_charlie_approval")
        from scripts.setup_charlie_approval import run_setup as charlie_setup
        await charlie_setup()
    elif "alice_hunter" in level_id:
        from scripts.setup_alice_lead import setup as alice_setup
        # If it is a coroutine or normal function
        if asyncio.iscoroutinefunction(alice_setup):
            await alice_setup()
        else:
            alice_setup()
    else:
        print(f"🧪 [Sandbox] Generic mock seeding completed for level {level_id}")

async def setup(level_id: str = "GENERIC_LEVEL", force_clean: bool = True):
    await run_setup(level_id, force_clean)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--level_id", default="GENERIC_LEVEL")
    parser.add_argument("--force_clean", default="true")
    args = parser.parse_args()
    
    setup(args.level_id, args.force_clean.lower() == "true")
