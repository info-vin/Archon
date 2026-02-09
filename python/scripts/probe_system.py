
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
        print("\n🧠 Running RAG Integrity Check (Librarian)...")
        result = await service.check_rag_integrity()

        status = result.get("status")
        details = result.get("details", {})

        if status == "healthy":
            print("✅ System Health: HEALTHY")
            print(f"   - Detected Dimensions: {details.get('detected_dimensions')}")
            print("   - Steps Passed:")
            for step in details.get("steps", []):
                print(f"     * {step}")
        else:
            print("❌ System Health: UNHEALTHY")
            print("   - Errors:")
            for err in details.get("errors", []):
                print(f"     ! {err}")

    except Exception as e:
        print(f"💥 Probe Crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_probe())
