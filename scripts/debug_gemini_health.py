import asyncio
import os
import sys

# Add python/src to path
sys.path.append(os.path.join(os.getcwd(), 'python', 'src'))

from server.services.credential_service import credential_service
from server.services.provider_discovery_service import provider_discovery_service

async def main():
    print("--- Starting Diagnostic ---")

    # 1. Check API Key
    try:
        api_key = await credential_service.get_credential("GOOGLE_API_KEY")
        if api_key:
            masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
            print(f"[OK] GOOGLE_API_KEY found: {masked_key}")
        else:
            print("[FAIL] GOOGLE_API_KEY not found in CredentialService")
            return
    except Exception as e:
        print(f"[ERROR] Failed to fetch credential: {e}")
        return

    # 2. Test Discovery
    try:
        print("--- Testing ProviderDiscoveryService ---")
        models = await provider_discovery_service.discover_google_models(api_key)

        if models:
            print(f"[OK] Discovered {len(models)} Google models.")
            for m in models:
                print(f"  - {m.name} ({m.provider})")
        else:
            print("[FAIL] No Google models discovered (empty list returned).")
            # Usually means non-200 response or network error caught internally

    except Exception as e:
        print(f"[ERROR] Discovery failed with exception: {e}")

    # 3. Test Manual Request (if needed for more detail)
    import aiohttp
    print("\n--- Manual Connectivity Check ---")
    base_url = "https://generativelanguage.googleapis.com/v1beta/models"
    headers = {"x-goog-api-key": api_key}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}?key={api_key}", headers=headers) as response:
                print(f"HTTP Status: {response.status}")
                if response.status != 200:
                    text = await response.text()
                    print(f"Response Body: {text}")
                else:
                    print("Connectivity successful.")
    except Exception as e:
        print(f"[ERROR] Connectivity check failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
