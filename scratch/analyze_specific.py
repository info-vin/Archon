import os
import sys
from datetime import datetime, UTC, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')))
from src.server.utils import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    # 2026-06-18 weekly report cost
    start_date = "2026-06-18T00:00:00+00:00"
    end_date = "2026-06-18T23:59:59+00:00"
    res = supabase.table("token_usage").select("*").gte("created_at", start_date).lte("created_at", end_date).execute()

    cost = 0.0
    tokens = 0
    runs = 0
    for r in res.data:
        ctx = r.get("context_type", "")
        if "agentic_workflow" in ctx or "weekly" in ctx or "summary" in ctx:
            cost += float(r.get("cost_usd", 0.0))
            tokens += int(r.get("input_tokens", 0)) + int(r.get("output_tokens", 0))
            runs += 1

    print(f"Weekly Report (2026-06-18) Cost: ${cost:.6f}, Tokens: {tokens}, Runs: {runs}")

if __name__ == "__main__":
    main()
