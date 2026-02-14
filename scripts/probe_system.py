import asyncio
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.server.config.logfire_config import logfire
from src.server.services.health_service import HealthService

# Configure logfire to avoid noise if not needed
logfire.configure(send_to_logfire='if-token-present')

async def run_probe():
    print("🏥 Archon System Probe Starting...")
    print("====================================")

    try:
        service = HealthService()

        # 1. Check basic DB connection
        print("🔌 Checking Database Connection...")
        if service.check_database_connection():
             print("✅ Database Connected")
        else:
             print("❌ Database Connection Failed")
             return

        # 2. Run Deep Integrity Check (RAG)
        print("\n🧠 Running System Integrity Check (Librarian)...")
        result = await service.check_rag_integrity()

        status = result.get("status")
        score = result.get("score", 0.0)
        details = result.get("details", {})

        status_emoji = "✅" if status == "healthy" else ("⚠️" if status == "degraded" else "❌")
        print(f"{status_emoji} System Status: {status.upper()}")
        print(f"📊 Integrity Score: {score}/100")
        
        print("\n🔍 Breakdown:")
        print(f"   - Knowledge Alignment: {details.get('alignment_raw', 0)}%")
        print(f"   - Search Responsiveness: {'ACTIVE' if details.get('search_active') else 'INACTIVE'}")
        print(f"   - Database Connectivity: {'CONNECTED' if details.get('db_connected') else 'DISCONNECTED'}")
        print(f"   - Total Sources: {details.get('total_sources', 0)}")
        print(f"   - Indexed Sources: {details.get('indexed_sources', 0)}")

        if "error" in details:
            print(f"\n💥 Error: {details['error']}")

        if status == "unhealthy":
            sys.exit(1)

    except Exception as e:
        print(f"💥 Probe Crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_probe())
