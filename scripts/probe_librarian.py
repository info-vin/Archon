
import asyncio
import os
import sys
from typing import List

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.server.services.search.rag_service import RAGService
from src.server.config.logfire_config import logfire

# Mock logger to avoid clutter
logfire.configure(send_to_logfire='if-token-present')

async def main():
    print("🤖 Bob (Marketing) is asking Librarian for inspiration...")
    
    query = "Data Analyst"
    print(f"🔍 Query: '{query}'")

    try:
        # Force model for diagnosis
        model_name = "gemini-embedding-001"
        print(f"DEBUG: FORCING Google embedding model to: '{model_name}'")
        
        # We need to monkeypatch the RAGService or its config temporarily for this probe
        # but a cleaner way is just to test the Librarian archiving directly first.
        
        # Step 0: Seed Data (Simulating Alice)
        print("\n--- Step 0: Seeding Data (Simulating Alice) ---")
        from src.server.services.librarian_service import LibrarianService
        librarian = LibrarianService()
        source_id = await librarian.archive_sales_pitch(
            company="Test Corp",
            job_title="Senior Data Analyst",
            content="We help Test Corp scale their data team with AI.",
            references=["test-ref"]
        )
        print(f"✅ Seeded document: {source_id}")
        
        rag = RAGService()
        
        # Test 1: Basic Retrieval (What does the Vector DB actually see?)
        # We search specifically for 'sales_pitch' to verify Alice's contribution
        print("\n--- Test 1: Context Retrieval ---")
        results = await rag.search_documents(
            query=query, 
            match_count=5, 
            filter_metadata={"knowledge_type": "sales_pitch"} # Correct argument name & filter logic
        )
        
        if not results:
            print("❌ No results found. Librarian is empty or indexing failed.")
            print("   Possible causes: Embedding failure, wrong filters, or data not committed.")
        else:
            print(f"✅ Found {len(results)} relevant items:")
            for item in results:
                print(f"   - [{item.metadata.get('knowledge_type', 'unknown')}] {item.title} (Score: {item.score:.4f})")
                print(f"     Preview: {item.content[:100]}...")

        # Test 2: Full RAG Generation (Can it write?)
        # This tests if the LLM can actually read the retrieved context
        print("\n--- Test 2: RAG Generation (Drafting) ---")
        # Note: In a real scenario, this calls generate_content with context.
        # For this probe, we just want to ensure retrieval works first.
        
    except Exception as e:
        print(f"💥 Probe crashed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ensure env vars are loaded (if running outside docker, this might need manual setup)
    # But we will run this via `docker exec`, so vars are present.
    asyncio.run(main())
