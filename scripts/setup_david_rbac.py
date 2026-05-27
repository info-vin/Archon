import asyncio
import os
import sys
from dotenv import load_dotenv

# Ensure python folder is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

for p in [".env", "python/.env", "../.env", "../python/.env"]:
    if os.path.exists(p):
        load_dotenv(p)

from src.server.utils import get_supabase_client

async def run_setup():
    print("🧪 Running David RBAC Matrix Pre-Hook...")
    supabase = get_supabase_client()
    
    # 1. Restore sales permissions to seeded state
    original_sales_perms = [
        'task:create', 
        'task:read:own', 
        'task:read:team', 
        'task:update:own', 
        'agent:trigger:mkt', 
        'leads:view:all', 
        'leads:view:sales', 
        'stats:view:own'
    ]
    
    try:
        supabase.table("archon_roles_permissions").update({
            "permissions": original_sales_perms
        }).eq("role", "sales").execute()
        print("Restored sales role permissions to default.")
    except Exception as e:
        print(f"Error resetting sales permissions: {e}")

async def setup():
    await run_setup()

if __name__ == "__main__":
    asyncio.run(run_setup())
