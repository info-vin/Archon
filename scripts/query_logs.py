import os
from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(url, key)

logs = supabase.table("archon_logs").select("*").order("created_at", desc=True).limit(20).execute()

for log in logs.data:
    print(f"[{log['created_at']}] {log['level']} - {log['source']}: {log['message']}")
    if log.get('details'):
        print(f"  Details: {str(log['details'])[:200]}...")
