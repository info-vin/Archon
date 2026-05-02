"""
Embedding Services

Handles all embedding-related operations.
"""

from .batch_processor import create_embeddings_batch
from .contextual_embedding_service import (
    generate_contextual_embedding,
    generate_contextual_embeddings_batch,
    process_chunk_with_context,
)
from .embedding_service import create_embedding, get_openai_client
from .models import EmbeddingBatchResult

__all__ = [
    # Embedding functions
    "create_embedding",
    "create_embeddings_batch",
    "get_openai_client",
    "EmbeddingBatchResult",
    # Contextual embedding functions
    "generate_contextual_embedding",
    "generate_contextual_embeddings_batch",
    "process_chunk_with_context",
]
