
import asyncio
import os
import sys

# Ensure we can import from src
# Archon/scripts -> need to see Archon/python
sys.path.append(os.path.join(os.path.dirname(__file__), '../python'))

from src.server.services.health_service import HealthService
from src.server.config.logfire_config import logfire

# Mock logger to avoid clutter
logfire.configure(send_to_logfire='if-token-present')

async def main():
    print("🤖 Archon: Running System-wide Health Probe (RAG + Dimensions)...")
    
    try:
        service = HealthService()
        result = await service.check_rag_integrity()
        
        status = result.get("status", "unknown")
        details = result.get("details", {})
        
        if status == "healthy":
            print("✅ SYSTEM PROBE PASSED.")
            print(f"   [Config] Model: {details.get('config', {}).get('model')} | Dims: {details.get('config', {}).get('dimensions')}")
            print(f"   [Integrity] Detected Dimensions: {details.get('detected_dimensions')}")
            sys.exit(0)
        elif status == "degraded":
            print("⚠️ SYSTEM PROBE DEGRADED.")
            for err in details.get("errors", []):
                print(f"   - {err}")
            sys.exit(0) # Exit code 0 if usable but degraded? Usually 0.
        else:
            print("❌ SYSTEM PROBE FAILED!")
            for err in details.get("errors", []):
                print(f"   - {err}")
            sys.exit(1)
            
    except Exception as e:
        print(f"💥 Probe execution crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
