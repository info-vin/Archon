import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

async def probe():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("Error: Missing credentials")
        return

    supabase = create_client(url, key)
    try:
        # Check if table exists by fetching 1 row
        result = supabase.table("archon_roles_permissions").select("role").limit(1).execute()
        print(f"✅ Table 'archon_roles_permissions' physically exists. Data count: {len(result.data)}")
    except Exception as e:
        if "does not exist" in str(e):
            print("❌ Table 'archon_roles_permissions' does not exist in the database.")
        else:
            print(f"⚠️ Error probing database: {e}")

if __name__ == "__main__":
    asyncio.run(probe())
