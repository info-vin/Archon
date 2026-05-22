import asyncio
import os
from dotenv import load_dotenv

# Load env variables
for p in [".env", "python/.env", "../.env"]:
    if os.path.exists(p):
        load_dotenv(p)

from supabase import create_client, Client

async def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_SERVICE_KEY not found.")
        return
        
    supabase: Client = create_client(url, key)
    
    # Query tasks that have "[Daily Report] Executive Summary" in title
    res = supabase.table("archon_tasks").select("id", "title", "description", "created_at").like("title", "[Daily Report] Executive Summary%").order("created_at", desc=True).limit(1).execute()
    print("Latest Executive Summary Task:")
    if res.data:
        task = res.data[0]
        print(f"Task ID: {task['id']}")
        print(f"Title: {task['title']}")
        print(f"Created At: {task['created_at']}")
        print("="*40)
        print(task['description'])
        print("="*40)
    else:
        print("No task found.")

if __name__ == "__main__":
    asyncio.run(main())
