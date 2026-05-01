from typing import Any
from ...config.logfire_config import get_logger
from ..embeddings.embedding_service import create_embedding

logger = get_logger(__name__)

class KnowledgeChunkingService:
    """
    Decoupled utility service for handling document chunking, embedding generation,
    and formatting into valid Vector DB page data.
    """
    def __init__(self, chunk_size: int = 4000):
        self.chunk_size = chunk_size

    async def process_document_into_pages(
        self,
        source_id: str,
        content: str,
        base_url: str,
        metadata: dict[str, Any],
        title_prefix: str
    ) -> list[dict]:
        """
        Splits content into chunks, generates embeddings for each,
        and returns a list of dictionaries ready to be inserted into `archon_crawled_pages`.
        """
        chunks = [content[i : i + self.chunk_size] for i in range(0, len(content), self.chunk_size)]
        page_data_list = []

        for i, chunk in enumerate(chunks):
            try:
                embedding_vector = await create_embedding(chunk)
            except Exception as e:
                logger.error(f"ChunkingService: Embedding failed for chunk {i} of {source_id}: {e}")
                embedding_vector = None

            # Create specific metadata for this chunk
            chunk_metadata = {**metadata, "title": f"{title_prefix} (Part {i + 1})"}

            page_data = {
                "source_id": source_id,
                "url": f"{base_url}#chunk={i}",
                "chunk_number": i,
                "content": chunk,
                "embedding": embedding_vector,
                "metadata": chunk_metadata,
            }
            page_data_list.append(page_data)

        return page_data_list
