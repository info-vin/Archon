"""
Storage Services

Handles document and code storage operations.
"""

from .base_storage_service import BaseStorageService
from .code.extraction import extract_code_blocks_logic as extract_code_blocks
from .code.summarization import generate_code_example_summary_logic as generate_code_example_summary
from .code_storage_service import add_code_examples_to_supabase
from .storage_services import DocumentStorageService

__all__ = [
    # Base service
    "BaseStorageService",
    # Service classes
    "DocumentStorageService",
    # Document storage utilities
    "DocumentStorageFacade",
    # Code storage utilities
    "extract_code_blocks",
    "generate_code_example_summary",
    "add_code_examples_to_supabase",
]
