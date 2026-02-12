
import asyncio
import os
import datetime
from python.src.server.utils import get_supabase_client
from python.src.server.services.health_service import HealthService

async def main():
    print("🚀 Manually triggering System Probe to fuel Integrity Chart...")
    health_service = HealthService()
    result = await health_service.check_rag_integrity()
    
    supabase = get_supabase_client()
    
    # Standardized Log Entry
    payload = {
        "source": "clockwork-scheduler",
        "level": "INFO" if result.get("status") == "healthy" else "ERROR",
        "message": f"System Probe: {result.get('status').upper()}",
        "details": result
    }
    
    res = supabase.table("archon_logs").insert(payload).execute()
    if res.data:
        print(f"✅ Log Entry Created: {res.data[0].get('id')}")
        print(f"📊 Real Integrity Score: {result.get('score')}%")
    else:
        print("❌ Failed to create log entry.")

if __name__ == "__main__":
    asyncio.run(main())
