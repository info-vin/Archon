import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.getcwd(), 'python', 'src'))

from server.utils import get_supabase_client
from server.services.embeddings.contextual_embedding_service import generate_contextual_embedding
from server.services.embeddings.embedding_service import create_embedding

async def deep_rag_optimize():
    client = get_supabase_client()
    print("🚀 Starting Deep RAG Optimization (Surgical Mode)...")
    
    # Only get chunks that NEED optimization
    res = client.table('archon_crawled_pages').select('id, content, source_id, metadata').filter('metadata->>contextual_embedding', 'is', 'null').execute()
    todo_chunks = res.data
    
    if not todo_chunks:
        print("✨ All chunks are already optimized!")
        return

    print(f"📦 Found {len(todo_chunks)} chunks to optimize.")
    total_optimized = 0
    
    # Group by source to avoid re-fetching full_doc unnecessarily
    source_groups = {}
    for chunk in todo_chunks:
        sid = chunk['source_id']
        if sid not in source_groups:
            source_groups[sid] = []
        source_groups[sid].append(chunk)

    for sid, chunks in source_groups.items():
        print(f"\n📂 Source: {sid}")
        # Fetch all chunks for this source to reconstruct full document context
        all_chunks_res = client.table('archon_crawled_pages').select('content').eq('source_id', sid).order('chunk_number').execute()
        full_doc = "\n".join([c['content'] for c in all_chunks_res.data])
        
        for chunk in chunks:
            print(f"  ⚡ Optimizing chunk {chunk['id']}...")
            new_content, success = await generate_contextual_embedding(full_doc, chunk['content'])
            
            if success:
                new_embedding = await create_embedding(new_content)
                metadata = chunk.get('metadata') or {}
                metadata['contextual_embedding'] = True
                metadata['original_content_before_contextual'] = chunk['content']
                
                client.table('archon_crawled_pages').update({
                    'content': new_content,
                    'embedding': new_embedding,
                    'metadata': metadata
                }).eq('id', chunk['id']).execute()
                total_optimized += 1
                print(f"    ✅ Success.")
            else:
                print(f"    ❌ Failed to generate contextual embedding.")
            
            # Small delay to respect rate limits even with retry logic
            await asyncio.sleep(2)
    
    print(f"\n✨ Deep RAG Optimization complete! Total chunks optimized: {total_optimized}")

if __name__ == "__main__":
    asyncio.run(deep_rag_optimize())
