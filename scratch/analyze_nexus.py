import os
import sys
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')))
from src.server.utils import get_supabase_client

def main():
    supabase = get_supabase_client()
    try:
        # Get count and cost
        res = supabase.table("token_usage").select("*").eq("context_type", "agent_nexusoracleagent").execute()
        records = res.data
    except Exception as e:
        print(f"Failed to query: {e}")
        return

    total_runs = len(records)
    total_cost = sum(float(r.get('cost_usd', 0.0)) for r in records)
    total_tokens = sum(int(r.get('input_tokens', 0)) + int(r.get('output_tokens', 0)) for r in records)

    print(f"NexusOracleAgent Total Runs: {total_runs}")
    print(f"NexusOracleAgent Total Tokens: {total_tokens}")
    print(f"NexusOracleAgent Total Cost (Theoretical): ${total_cost:.6f}")

if __name__ == "__main__":
    main()
