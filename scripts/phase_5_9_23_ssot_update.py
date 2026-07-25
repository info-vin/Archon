import asyncio
import os
import sys

# Setup python path to allow importing src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../python')))

from src.server.services.credential_service import set_credential

async def update_ssot():
    print("🚀 Updating SSOT settings for Phase 5.9.23...")
    
    # 1. Update EMBEDDING_DIMENSIONS to 768
    success_dim = await set_credential(
        key="EMBEDDING_DIMENSIONS",
        value="768",
        category="rag_strategy",
        description="Global vector dimension SSOT. Forced to 768 to match pgvector columns.",
        is_encrypted=False
    )
    if success_dim:
        print("✅ EMBEDDING_DIMENSIONS successfully set to 768.")
    else:
        print("❌ Failed to set EMBEDDING_DIMENSIONS.")

    # 2. Update USE_AGENTIC_RAG to true
    success_rag = await set_credential(
        key="USE_AGENTIC_RAG",
        value="true",
        category="rag_strategy",
        description="Enable Agentic RAG for code example search.",
        is_encrypted=False
    )
    if success_rag:
        print("✅ USE_AGENTIC_RAG successfully set to true.")
    else:
        print("❌ Failed to set USE_AGENTIC_RAG.")

if __name__ == "__main__":
    asyncio.run(update_ssot())
