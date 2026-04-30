"""
Utility functions for the Crawl4AI MCP server - Compatibility Layer

This file now serves as a compatibility layer, importing functions from
the new service modules to maintain backward compatibility.

The actual implementations have been moved to:
- services/embeddings/ - Embedding operations
- services/storage/ - Document and code storage
- services/search/ - Vector search operations
- services/source_management_service.py - Source metadata
- services/client_manager.py - Client connections
"""

# Import all functions from new services for backward compatibility

# Keep some imports that are still needed
from ..services.client_manager import get_supabase_client
# Note: storage and search imports removed to avoid circular dependency
# Import these directly from their modules when needed:
# from ..services.storage import add_documents_to_supabase, extract_code_blocks, etc.
# from ..services.search import search_documents, search_code_examples

# Export all imported functions for backward compatibility
__all__ = [
    # Client functions
    "get_supabase_client",
]
