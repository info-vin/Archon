from typing import Any
from ..config.logfire_config import get_logger

logger = get_logger(__name__)

class KnowledgeRepository:
    """
    Repository for handling persistence of knowledge items (Vector DB and Audit Trail).
    Decoupled from LibrarianService during Phase 4.6.50 God Object Refactoring.
    """
    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def insert_crawled_page(self, page_data: dict | list[dict]) -> bool:
        """
        Inserts one or multiple chunked pages into the vector store.
        """
        try:
            if isinstance(page_data, list):
                if not page_data:
                    return True
                self.supabase.table("archon_crawled_pages").insert(page_data).execute()
            else:
                self.supabase.table("archon_crawled_pages").insert(page_data).execute()
            return True
        except Exception as e:
            logger.error(f"KnowledgeRepository: Failed to insert crawled page(s): {e}")
            return False

    def insert_document_version(self, document_id: str, field_name: str, change_summary: str, content: dict, created_by: str) -> bool:
        """
        Records an audit trail / version history for the newly created or updated knowledge.
        """
        try:
            self.supabase.table("archon_document_versions").insert(
                {
                    "document_id": document_id,
                    "field_name": field_name,
                    "change_type": "create",
                    "change_summary": change_summary,
                    "content": content,
                    "created_by": created_by,
                    "version_number": 1,
                }
            ).execute()
            return True
        except Exception as e:
            logger.warning(f"KnowledgeRepository: Failed to log document version: {e}")
            return False
