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
    print("🚀 Starting Deep RAG Optimization (Contextual Retrieval)...")
    
    # 1. Fetch all unique source_ids from archon_crawled_pages
    res = client.table('archon_crawled_pages').select('source_id').execute()
    source_ids = list(set([r['source_id'] for r in res.data]))
    print(f"Found {len(source_ids)} sources to optimize.")
    
    total_optimized = 0
    
    for sid in source_ids:
        print(f"\nProcessing source: {sid}")
        # 2. Fetch all chunks for this source, ordered by chunk_number
        chunks_res = client.table('archon_crawled_pages').select('*').eq('source_id', sid).order('chunk_number').execute()
        chunks = chunks_res.data
        
        if not chunks:
            continue
            
        # 3. Reconstruct full document
        full_doc = "\n".join([c['content'] for c in chunks])
        print(f"Reconstructed full document ({len(full_doc)} chars, {len(chunks)} chunks)")
        
        for chunk in chunks:
            cid = chunk['id']
            if chunk.get('metadata', {}).get('contextual_embedding'):
                print(f"  Chunk {chunk['chunk_number']} already optimized. Skipping.")
                continue
            
            print(f"  Situating chunk {chunk['chunk_number']}...")
            
            # Retry loop for 429 handling
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    contextual_content, success = await generate_contextual_embedding(full_doc, chunk['content'])
                    
                    if success:
                        new_embedding = await create_embedding(contextual_content)
                        metadata = chunk.get('metadata') or {}
                        metadata['contextual_embedding'] = True
                        metadata['original_content_before_contextual'] = chunk['content']
                        
                        client.table('archon_crawled_pages').update({
                            'content': contextual_content,
                            'embedding': new_embedding,
                            'metadata': metadata
                        }).eq('id', cid).execute()
                        
                        total_optimized += 1
                        print(f"  ✅ Chunk {chunk['chunk_number']} optimized.")
                        break
                    else:
                        print(f"  ⚠️ Attempt {attempt+1} failed to generate context.")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(5)
                except Exception as e:
                    if "429" in str(e) or "quota" in str(e).lower():
                        print(f"  ⏳ Rate limit hit. Waiting 60s (Attempt {attempt+1}/{max_retries})...")
                        await asyncio.sleep(60)
                    else:
                        print(f"  ❌ Error: {e}")
                        break
    
    print(f"\n✨ Deep RAG Optimization complete! Total chunks optimized: {total_optimized}")

if __name__ == "__main__":
    asyncio.run(deep_rag_optimize())
