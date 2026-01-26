
import asyncio
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.server.services.credential_service import credential_service
from src.server.config.logfire_config import logfire

# Mock logger to avoid clutter
logfire.configure(send_to_logfire='if-token-present')

async def force_google_config():
    print("🔧 Forcing RAG Configuration to GOOGLE / GEMINI-001 (768 dim)...")
    
    settings = {
        "LLM_PROVIDER": "google",
        "EMBEDDING_PROVIDER": "google", 
        "EMBEDDING_MODEL": "gemini-embedding-001",
        "EMBEDDING_DIMENSIONS": "768",
        # Clear fallbacks to ensure purity
        "EMBEDDING_PROVIDER_FALLBACK": "",
        "EMBEDDING_MODEL_FALLBACK": "",
    }
    
    for key, value in settings.items():
        print(f"   -> Setting {key} = {value}")
        await credential_service.set_credential(
            key, value, category="rag_strategy", description="Forced by validation script"
        )
        
    print("✅ Configuration updated. Verifying...")
    
    # Validation
    configs = await credential_service.get_embedding_provider_configs()
    primary = configs[0] if configs else {}
    
    if primary.get("provider") == "google" and primary.get("embedding_model") == "gemini-embedding-001":
        print("🎉 SUCCESS: System is now configured for Google RAG.")
    else:
        print(f"❌ FAILURE: Verification failed. Current primary config: {primary}")

if __name__ == "__main__":
    asyncio.run(force_google_config())
