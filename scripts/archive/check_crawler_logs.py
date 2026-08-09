
import sys
import os
from datetime import datetime, timedelta

# Add python source to path
sys.path.append(os.path.join(os.getcwd(), "python"))

from src.server.utils import get_supabase_client

def check_crawler_logs():
    client = get_supabase_client()
    
    # Yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Checking logs for: {yesterday}")
    
    # Query logs for crawler sources
    # Sources: crawler, job104, job_board
    # Filters: ERROR level or message containing 429/503
    
    sources = ["crawler", "job104", "job_board"]
    
    query = (
        client.table("archon_logs")
        .select("*")
        .in_("source", sources)
        .gte("created_at", f"{yesterday}T00:00:00")
        .lt("created_at", f"{yesterday}T23:59:59")
        .order("created_at", desc=True)
    )
    
    response = query.execute()
    logs = response.data
    
    print(f"Found {len(logs)} log entries.")
    
    error_logs = [
        log for log in logs 
        if log.get("level") == "ERROR" or 
           "429" in str(log.get("details", "")) or 
           "503" in str(log.get("details", ""))
    ]
    
    print(f"Found {len(error_logs)} error log entries (429/503/ERROR).")
    
    for log in error_logs[:20]:
        print(f"---")
        print(f"Time: {log.get('created_at')}")
        print(f"Source: {log.get('source')}")
        print(f"Message: {log.get('message')}")
        print(f"Details: {log.get('details')}")

if __name__ == "__main__":
    check_crawler_logs()
