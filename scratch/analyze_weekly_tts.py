import os
import sys
from datetime import datetime, UTC, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')))
from src.server.utils import get_supabase_client

def main():
    supabase = get_supabase_client()
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=14)
    
    # Check Librarian_TTS
    res_tts = supabase.table("token_usage").select("*").eq("context_type", "Librarian_TTS").order('created_at', desc=True).limit(5).execute()
    
    # Check agentic_workflow or weekly report related
    res_weekly = supabase.table("token_usage").select("*").gte("created_at", start_date.isoformat()).execute()

    # also check archon_tasks for weekly reports
    res_tasks = supabase.table("archon_tasks").select("id, title, description, created_at").ilike("title", "%Weekly Report%").order('created_at', desc=True).limit(3).execute()

    print("--- RECENT TTS EXECUTIONS ---")
    for r in res_tts.data:
        print(f"Date: {r['created_at']}, Tokens: {r['input_tokens']}+{r['output_tokens']}, Cost: ${r['cost_usd']}")

    print("\n--- RECENT WEEKLY REPORTS (Tasks) ---")
    for r in res_tasks.data:
        print(f"Date: {r['created_at']}, Title: {r['title']}")

    print("\n--- TOKEN USAGE GROUPED BY CONTEXT (LAST 7 DAYS) ---")
    d7 = end_date - timedelta(days=7)
    ctx_map = {}
    for r in res_weekly.data:
        # only look at last 7 days
        dt = datetime.fromisoformat(r['created_at'].replace('Z', '+00:00'))
        if dt < d7: continue
        ctx = r.get('context_type') or 'unknown'
        if ctx not in ctx_map:
            ctx_map[ctx] = {'cost':0.0, 'tokens':0, 'count':0}
        ctx_map[ctx]['cost'] += float(r.get('cost_usd', 0.0))
        ctx_map[ctx]['tokens'] += int(r.get('input_tokens', 0)) + int(r.get('output_tokens', 0))
        ctx_map[ctx]['count'] += 1
        
    for k, v in ctx_map.items():
        print(f"CTX: {k} | Runs: {v['count']} | Cost: ${v['cost']:.6f} | Tokens: {v['tokens']}")

if __name__ == "__main__":
    main()
