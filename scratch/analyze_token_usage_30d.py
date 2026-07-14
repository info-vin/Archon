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
    start_date = end_date - timedelta(days=60)
    
    try:
        res = supabase.table("token_usage").select("*").gte("created_at", start_date.isoformat()).execute()
        records = res.data
    except Exception as e:
        print(f"Failed to query token_usage: {e}")
        return

    total_cost = 0.0
    total_tokens = 0
    models_stats = {}
    context_stats = {}

    for r in records:
        cost = float(r.get('cost_usd', 0.0))
        inp = int(r.get('input_tokens', 0))
        outp = int(r.get('output_tokens', 0))
        model = r.get('model', 'unknown')
        ctx = r.get('context_type') or 'unknown'

        total_cost += cost
        total_tokens += (inp + outp)

        if model not in models_stats:
            models_stats[model] = {'cost': 0.0, 'inp': 0, 'outp': 0}
        models_stats[model]['cost'] += cost
        models_stats[model]['inp'] += inp
        models_stats[model]['outp'] += outp

        if ctx not in context_stats:
            context_stats[ctx] = {'cost': 0.0, 'tokens': 0}
        context_stats[ctx]['cost'] += cost
        context_stats[ctx]['tokens'] += (inp + outp)

    print(f"Total Cost: {total_cost:.6f}")
    print("--- MODEL STATS ---")
    for m, s in sorted(models_stats.items(), key=lambda x: x[1]['cost'], reverse=True):
        pct = (s['cost'] / total_cost * 100) if total_cost > 0 else 0
        daily = s['cost'] / 30.0
        print(f"MODEL: {m} | Cost: ${s['cost']:.6f} ({pct:.1f}%) | Daily: ${daily:.6f} | Tokens: In {s['inp']}, Out {s['outp']}")

    print("--- CONTEXT STATS ---")
    for c, s in sorted(context_stats.items(), key=lambda x: x[1]['cost'], reverse=True):
        pct = (s['cost'] / total_cost * 100) if total_cost > 0 else 0
        print(f"CTX: {c} | Cost: ${s['cost']:.6f} ({pct:.1f}%) | Tokens: {s['tokens']}")

if __name__ == "__main__":
    main()
