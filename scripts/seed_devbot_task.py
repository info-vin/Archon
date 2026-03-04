import os
import asyncio
from datetime import datetime, timedelta
from supabase import create_client, Client

# Add project root to path for imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../python")))

from src.server.services.agent_service import agent_service
from src.server.config.logfire_config import setup_logfire

async def main():
    setup_logfire()
    url = os.environ.get("SUPABASE_URL", "http://127.0.0.1:8000")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    if not key:
        print("Missing SUPABASE_SERVICE_KEY")
        return
        
    print(f"Connecting to Supabase at {url}")
    supabase: Client = create_client(url, key)
    
    # 1. Prepare Realistic Prompt for DevBot
    task_title = "Please analyze the 'scripts/' directory and suggest which debug scripts are safe to delete."
    
    # Get first project ID
    resp = supabase.table("archon_projects").select("id").limit(1).execute()
    if not resp.data:
        proj_resp = supabase.table("archon_projects").insert({"title": "Archon System Maintenance", "description": ""}).execute()
        proj_id = proj_resp.data[0]["id"]
    else:
        proj_id = resp.data[0]["id"]
        
    # Get DevBot UUID
    devbot_id = None
    devbot_resp = supabase.table("profiles").select("id").eq("email", "dev.bot@archon.com").execute()
    if devbot_resp.data:
        devbot_id = devbot_resp.data[0]["id"]
    else:
        print("Error: DevBot profile not found in DB.")
        return
        
    # 2. Insert the Task
    task = {
        "project_id": proj_id,
        "title": task_title,
        "description": "Examine the local python scripts for redundant telemetry files.",
        "status": 'todo',
        "priority": 'medium',
        "assignee_id": devbot_id,
        "task_order": 999
    }
    
    task_resp = supabase.table("archon_tasks").insert(task).execute()
    if not task_resp.data:
        print("Failed to insert task.")
        return
        
    task_id = task_resp.data[0]["id"]
    print(f"✅ Created Task ID: {task_id}")
    
    # 3. Physically Execute DevBot (Trigger LLM via Server Backend)
    print("🚀 Triggering precise DevBot LLM execution...")
    await agent_service.run_agent_task(task_id, "ai-dev-bot")
    
    # 4. Verify the output
    done_task = supabase.table("archon_tasks").select("status, attachments").eq("id", task_id).execute()
    if done_task.data and done_task.data[0]["status"] in ["done", "completed"]:
        print("\n🎉 DevBot Execution Successful! XP Awarded.")
        attachments = done_task.data[0].get('attachments', [])
        if attachments and isinstance(attachments, list) and len(attachments) > 0:
            final_content = attachments[-1].get("output", {}).get("content", "No content found")
            print(f"DevBot's Conclusion:\n{final_content}")
        else:
            print("DevBot finished but no attachments/output was found.")
    else:
        print(f"\n❌ DevBot Execution Failed or Pending. Status: {done_task.data[0].get('status')}")

if __name__ == "__main__":
    asyncio.run(main())
