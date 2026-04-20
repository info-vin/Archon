import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.join(os.getcwd(), 'python', 'src'))

from server.utils import get_supabase_client
from server.services.embeddings.contextual_embedding_service import generate_contextual_embeddings_batch
from server.services.embeddings.embedding_service import create_embedding

async def deep_rag_optimize():
    client = get_supabase_client()
    print("🚀 Starting Deep RAG Optimization (Batch Mode)...")
    
    res = client.table('archon_crawled_pages').select('source_id').execute()
    source_ids = list(set([r['source_id'] for r in res.data]))
    
    for sid in source_ids:
        chunks_res = client.table('archon_crawled_pages').select('*').eq('source_id', sid).order('chunk_number').execute()
        all_chunks = chunks_res.data
        if not all_chunks: continue
            
        full_doc = "\n".join([c['content'] for c in all_chunks])
        
        # Filter only those that need optimization
        todo_chunks = [c for c in all_chunks if not (c.get('metadata') or {}).get('contextual_embedding')]
        if not todo_chunks: continue
        
        print(f"\n📦 Processing {len(todo_chunks)} chunks for source: {sid}")
        
        # Process in batches of 10 to minimize API calls (Anti-429)
        batch_size = 10
        for i in range(0, len(todo_chunks), batch_size):
            batch = todo_chunks[i:i+batch_size]
            print(f"  Sending Batch {i//batch_size + 1} ({len(batch)} chunks)...")
            
            # Use the existing batch function
            results = await generate_contextual_embeddings_batch([full_doc]*len(batch), [c['content'] for c in batch])
            
            for chunk, (new_content, success) in zip(batch, results):
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
            
            print(f"  ✅ Batch {i//batch_size + 1} processed.")
            # Wait 10s between batches to safely stay under Free Tier RPM
            await asyncio.sleep(10)
    
    print(f"\n✨ Deep RAG Optimization complete! Total chunks optimized: {total_optimized}")

if __name__ == "__main__":
    asyncio.run(deep_rag_optimize())
