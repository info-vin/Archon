import os
import sys
from datetime import datetime, UTC, timedelta
import statistics
from dotenv import load_dotenv

# Add the root directory to sys.path to allow importing from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'python')))

# Load .env
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env')))

from src.server.utils import get_supabase_client

def main():
    supabase = get_supabase_client()
    
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=60)
    
    try:
        res = supabase.table("token_usage").select("cost_usd, created_at").gte("created_at", start_date.isoformat()).execute()
        records = res.data
    except Exception as e:
        print(f"Failed to query token_usage: {e}")
        return

    daily_costs = {}
    for i in range(60):
        d = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
        daily_costs[d] = 0.0
        
    for r in records:
        dt_str = r['created_at'].split('T')[0]
        if dt_str in daily_costs:
            daily_costs[dt_str] += float(r.get('cost_usd', 0.0))
            
    def get_stats(days):
        costs = []
        for i in range(days):
            d = (end_date - timedelta(days=i)).strftime('%Y-%m-%d')
            costs.append(daily_costs.get(d, 0.0))
            
        mean_cost = statistics.mean(costs) if costs else 0.0
        stdev_cost = statistics.stdev(costs) if len(costs) > 1 else 0.0
        return mean_cost, stdev_cost
        
    mean7, std7 = get_stats(7)
    mean30, std30 = get_stats(30)
    mean60, std60 = get_stats(60)
    
    print(f"7_Days: Mean={mean7:.6f}, Std={std7:.6f}")
    print(f"30_Days: Mean={mean30:.6f}, Std={std30:.6f}")
    print(f"60_Days: Mean={mean60:.6f}, Std={std60:.6f}")

if __name__ == "__main__":
    main()
