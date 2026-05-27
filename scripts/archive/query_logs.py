import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

logs = supabase.table("archon_logs").select("*").neq("level", "INFO").order("created_at", desc=True).limit(50).execute()

for log in logs.data:
    print(f"[{log['created_at']}] {log['level']} - {log['source']}: {log['message']}")
    if log.get('details'):
        print(f"  Details: {str(log['details'])[:200]}...")
