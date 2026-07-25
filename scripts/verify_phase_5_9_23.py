import asyncio
import os
import sys

# Setup python path to allow importing src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../python')))

from src.server.services.client_manager import get_supabase_client
import httpx

async def verify():
    print("🔍 Starting Phase 5.9.23 Verification...")
    client = get_supabase_client()

    # 1. Verify Vector Dimension 768 against Database
    print("\n--- 1. Vector Dimension Verification ---")
    try:
        # Create a 768-dimensional zero vector
        test_vector = [0.0] * 768
        res = client.rpc('match_archon_crawled_pages', {
            'query_embedding': test_vector,
            'match_count': 1
        }).execute()
        print("✅ SUCCESS: RPC match_archon_crawled_pages executed correctly with a 768-dimensional vector.")
        print(f"Data returned count: {len(res.data) if res.data else 0}")
    except Exception as e:
        print(f"❌ ERROR: Vector dimension test failed. {e}")
        return False

    # 2. Verify Agentic RAG Endpoint
    print("\n--- 2. Agentic RAG Endpoint Verification ---")
    try:
        from src.server.services.search.rag_service import RAGService
        service = RAGService(client)
        success, result = await service.search_code_examples_service(
            query="test",
            source_id=None
        )
        if success:
            print("✅ SUCCESS: search_code_examples_service returned successfully.")
        else:
            print(f"❌ ERROR: Service returned failure: {result}")
            return False
    except Exception as e:
        print(f"❌ ERROR: Could not execute RAG service. {e}")
        return False

    print("\n🎉 All verifications passed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(verify())
    if not success:
        sys.exit(1)
