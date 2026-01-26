
import asyncio
import os
import sys
from typing import List

# Ensure we can import from src
# Ensure we can import from src
# We are in Archon/scripts, we need Archon/python in path to see 'src'
sys.path.append(os.path.join(os.path.dirname(__file__), '../python'))

from src.server.services.search.rag_service import RAGService
from src.server.config.logfire_config import logfire

# Mock logger to avoid clutter
logfire.configure(send_to_logfire='if-token-present')

async def run_probe_logic():
    print("🤖 Clockwork: Starting scheduled system probe...")
    
    query = "Data Analyst"
    # print(f"🔍 Query: '{query}'") # Reduce noise

    try:
        # Force model for diagnosis
        # Smart Probe: Fetch actual config from DB
        from src.server.services.credential_service import credential_service
        
        # print("🔍 probing system configuration...")
        rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
        
        provider = rag_settings.get("EMBEDDING_PROVIDER") or rag_settings.get("LLM_PROVIDER") or "openai"
        model_name = rag_settings.get("EMBEDDING_MODEL") or "text-embedding-3-small"
        dimensions_str = rag_settings.get("EMBEDDING_DIMENSIONS", "1536")
        
        # print(f"DEBUG: System Configured Model: '{model_name}' (Provider: {provider}, Dimensions: {dimensions_str})")
        
        expected_dim = int(dimensions_str)
        # Verify assumptions
        if "gemini" in model_name and expected_dim != 768:
             print(f"⚠️ WARNING: Model is '{model_name}' but dimensions set to {expected_dim}. Gemini usually uses 768.")
        if "large" in model_name and expected_dim != 3072:
             print(f"⚠️ WARNING: Model is '{model_name}' but dimensions set to {expected_dim}. OpenAI Large usually uses 3072.")
        
        # Step 0: Seed Data (Simulating Alice)
        # print("\n--- Step 0: Seeding Data (Simulating Alice) ---")
        from src.server.services.librarian_service import LibrarianService
        librarian = LibrarianService()
        source_id = await librarian.archive_sales_pitch(
            company="Test Corp",
            job_title="Senior Data Analyst",
            content="We help Test Corp scale their data team with AI.",
            references=["test-ref"]
        )
        # print(f"✅ Seeded document: {source_id}")
        
        # Integrity Check: Verify Embedding Dimensions
        # print("\n--- Step 0.5: Integrity Check (Dimensions) ---")
        
        # Check DB directly first to see if embedding exists (it might be async)
        max_retries = 5
        # print(f"⏳ Waiting for embedding generation (max {max_retries * 2}s)...")
        
        raw_embedding = None
        for i in range(max_retries):
            db_item = librarian.supabase.table("archon_crawled_pages").select("embedding").eq("source_id", source_id).limit(1).execute()
            if db_item.data and db_item.data[0].get("embedding"):
                raw_embedding = db_item.data[0].get("embedding")
                # print(f"✅ Embedding found in DB (Attempt {i+1})")
                break
            # print(f"   Attempt {i+1}: Embedding not ready yet...")
            await asyncio.sleep(2)
            
        if raw_embedding:
            # Parse string '[...]' or list if it's already JSON parsed
            if isinstance(raw_embedding, str):
                import json
                vec = json.loads(raw_embedding)
            else:
                vec = raw_embedding
                
            dim = len(vec)
            # print(f"📊 Detected Vector Dimension: {dim}")
            
            if dim != expected_dim:
                print(f"❌ CRITICAL WARNING: Dimension Mismatch! Config expects {expected_dim}, but database has {dim}.")
                print("   This indicates data pollution or model configuration error.")
                return False
            else:
                pass
                # print(f"✅ Dimension Check Passed: {dim} matches expected for '{model_name}'")
        else:
             print("❌ CRITICAL: Embedding was never generated in the DB. Check DB triggers or background workers.")
             return False

        rag = RAGService()
        
        # Test 1: Context Retrieval (What does the Vector DB actually see?)
        # We search specifically for 'sales_pitch' to verify Alice's contribution
        # print("\n--- Test 1: Context Retrieval ---")
        results = await rag.search_documents(
            query=query, 
            match_count=5, 
            filter_metadata={"knowledge_type": "sales_pitch"} # Correct argument name & filter logic
        )
        
        if not results:
            print("❌ No results found. Librarian is empty or indexing failed.")
            print("   Possible causes: Embedding failure, wrong filters, or data not committed.")
            return False
        else:
            # print(f"✅ Found {len(results)} relevant items:")
            pass

        print("✅ Clockwork: System Probe Passed.")
        return True
        
    except Exception as e:
        print(f"💥 Probe crashed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Ensure env vars are loaded (if running outside docker, this might need manual setup)
    # But we will run this via `docker exec`, so vars are present.
    asyncio.run(run_probe_logic())
