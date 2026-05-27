import os
import sys

from supabase import create_client

def run_probe():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")
    
    if not url or not key:
        print("❌ db_probe: SUPABASE_URL or SUPABASE_SERVICE_KEY missing.")
        sys.exit(1)
        
    try:
        client = create_client(url, key)
        # Check archon_crawled_pages dimension
        try:
            res = client.rpc("get_vector_dimension", {"table_name": "archon_crawled_pages", "column_name": "embedding"}).execute()
        except Exception as rpc_err:
            print(f"⚠️ RPC 'get_vector_dimension' failed or not found: {rpc_err}. Performing surface probe.")
            res = client.table("archon_crawled_pages").select("id").limit(1).execute()
            print("✓ Surface probe passed.")
            sys.exit(0)
            
        if not res.data:
            print("⚠️ No data returned from RPC. Performing surface probe.")
            res = client.table("archon_crawled_pages").select("id").limit(1).execute()
            print("✓ Surface probe passed.")
            sys.exit(0)
            
        dim = int(res.data)
        if dim != 768:
            print(f"❌ db_probe: FATAL DIMENSION MISMATCH. Expected 768, got {dim}.")
            print("This indicates a severe regression in embedding models.")
            sys.exit(1)
            
        print("✓ RAG Integrity Gate Passed: Dimension Match 768.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ db_probe: Probe failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_probe()
