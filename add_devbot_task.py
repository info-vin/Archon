import os
import asyncio
from supabase import create_client, Client

async def main():
    url = os.environ.get("SUPABASE_URL", "http://supabase-kong:8000")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "your-service-key")
    
    # If run inside the container, SUPABASE_URL and KEY are preset.
    supabase: Client = create_client(url, key)
    
    # Get first project ID
    resp = supabase.table("archon_projects").select("id").limit(1).execute()
    if not resp.data:
        print("No project found.")
        return
    proj_id = resp.data[0]["id"]
    
    # Read the markdown file
    with open('/app/PRPs/DevBot_L1_Loading_Fix.md', 'r') as f:
        desc = f.read()
        
    # Insert task
    task = {
        "project_id": proj_id,
        "title": 'L1 Mission: Fix "Loading..." Infinite Render',
        "description": desc,
        "status": 'todo',  # or 'open', wait seed_mock_data.sql used 'todo', 'in_progress', 'done'
        "priority": 'high',
        "assignee": 'DevBot',
        "task_order": 999
    }
    
    # Check if exists to be idempotent
    check_resp = supabase.table("archon_tasks").select("id").eq("title", task["title"]).execute()
    if check_resp.data:
        print("Task already exists, updating...")
        supabase.table("archon_tasks").update(task).eq("id", check_resp.data[0]["id"]).execute()
    else:
        print("Inserting new DevBot task...")
        supabase.table("archon_tasks").insert(task).execute()
        
    print("DevBot Task successfully prepared in DB!")

if __name__ == "__main__":
    asyncio.run(main())
