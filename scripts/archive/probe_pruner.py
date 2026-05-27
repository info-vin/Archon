import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))

# Ensure python/src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../python/src')))

from server.services.enrichment_service import EnrichmentService
from server.utils import get_supabase_client

async def main():
    print("🚀 [Probe] Starting prune_stale_leads verification...")
    supabase = get_supabase_client()
    
    # 1. Create a dummy stale lead
    print("📝 Inserting dummy stale lead...")
    old_date = (datetime.now() - timedelta(days=5)).isoformat()
    res = supabase.table("leads").insert({
        "job_title": "Probe Stale Lead",
        "company_name": "Probe Inc.",
        "description_snippet": "This is a test lead for the pruner.",
        "status": "new",
        "enrichment_score": 10,
        "created_at": old_date,
        "source_job_url": "https://example.com/probe"
    }).execute()
    
    if not res.data:
        print("❌ Failed to insert test lead.")
        return
        
    lead_id = res.data[0]["id"]
    print(f"✅ Inserted test lead with ID: {lead_id} (Score: 10, Created: {old_date})")
    
    # 2. Run the pruner
    print("⚙️ Running EnrichmentService.prune_stale_leads()...")
    pruned_count = await EnrichmentService.prune_stale_leads()
    print(f"✅ Pruner reported {pruned_count} records updated.")
    
    # 3. Verify the lead status
    print("🔍 Verifying lead status...")
    verify_res = supabase.table("leads").select("status, auto_archived_reason").eq("id", lead_id).execute()
    
    if verify_res.data:
        lead = verify_res.data[0]
        if lead["status"] == "archived" and lead["auto_archived_reason"] == "stale_low_quality":
            print(f"✅ SUCCESS: Lead was successfully archived by the background task logic.")
        else:
            print(f"❌ FAILURE: Lead status is '{lead['status']}', reason: '{lead['auto_archived_reason']}'. Expected 'archived'.")
    else:
        print("❌ FAILURE: Could not find lead after pruning.")
        
    # Cleanup
    print("🧹 Cleaning up probe lead...")
    supabase.table("leads").delete().eq("id", lead_id).execute()
    print("✅ Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())
