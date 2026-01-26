
import asyncio
import os
import sys

# Ensure we can import from src
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.server.services.search.rag_service import RAGService
from src.server.config.logfire_config import logfire

# Mock logger to avoid clutter
logfire.configure(send_to_logfire='if-token-present')

async def probe_rag():
    print("🔍 Probing RAG Service for MarketBot Integration...")
    
    try:
        rag = RAGService()
        query = "Test Corp"
        
        # Test retrieval with specific filter (simulating MarketBot looking for pitches)
        print(f"   Searching for: '{query}' with filter knowledge_type='sales_pitch'")
        
        success, result = await rag.perform_rag_query(
            query=query, 
            match_count=3,
            filter_metadata={"knowledge_type": "sales_pitch"}
        )
        
        if success and result.get("results"):
            print(f"✅ RAG Retrieval Successful! Found {len(result['results'])} items.")
            for item in result['results']:
                print(f"   - {item.get('content', '')[:50]}...")
        else:
            print("⚠️ RAG Retrieval returned no results (or failed).")
            print(f"   Debug Info: Success={success}, Result Keys={result.keys() if result else 'None'}")
            
    except Exception as e:
        print(f"💥 RAG Service Initialization Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(probe_rag())
