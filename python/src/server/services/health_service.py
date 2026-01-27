import asyncio
import json

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client
from .credential_service import credential_service
from .librarian_service import LibrarianService
from .search.rag_service import RAGService

logger = get_logger(__name__)

class HealthService:
    """Service for checking the health of the application and its dependencies."""

    def __init__(self):
        self.supabase_client = get_supabase_client()

    def check_database_connection(self) -> bool:
        """Checks if the database connection is active."""
        try:
            # A simple query to check the connection
            self.supabase_client.table("users").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False

    def check_table_existence(self, table_name: str) -> bool:
        """Checks if a specific table exists in the database."""
        try:
            # Note: This is a simplified check. A more robust check might involve
            # querying information_schema, but for this purpose, a select is sufficient.
            self.supabase_client.table(table_name).select("id").limit(1).execute()
            return True
        except Exception:
            # The query will fail if the table does not exist
            return False

    def get_system_health(self) -> dict:
        """Returns a comprehensive health status of the system."""
        db_connected = self.check_database_connection()

        if not db_connected:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "services": {}
            }

        # List of essential tables to check
        tables_to_check = ["projects", "tasks", "profiles", "gemini_logs"]

        table_statuses = {}
        all_tables_ok = True
        for table in tables_to_check:
            exists = self.check_table_existence(table)
            table_statuses[f"{table}_table"] = exists
            if not exists:
                all_tables_ok = False

        system_status = "healthy" if all_tables_ok else "degraded"

        return {
            "status": system_status,
            "database": "connected",
            "services": {
                "schema": {
                    **table_statuses,
                    "valid": all_tables_ok
                }
            }
        }

    async def check_rag_integrity(self) -> dict:
        """
        Performs a deep integrity check of the RAG system.
        Ported from scripts/probe_librarian.py.
        Includes: Config check, Seeding (Test Data), DB Integrity, Retrieval Test.
        """
        logger.info("Starting RAG integrity check...")

        details = {
            "steps": [],
            "config": {},
            "errors": []
        }

        try:
            # 1. Config Check
            rag_settings = await credential_service.get_credentials_by_category("rag_strategy")
            provider = rag_settings.get("EMBEDDING_PROVIDER") or rag_settings.get("LLM_PROVIDER") or "openai"
            model_name = rag_settings.get("EMBEDDING_MODEL") or "text-embedding-3-small"
            dimensions_str = rag_settings.get("EMBEDDING_DIMENSIONS", "1536")
            expected_dim = int(dimensions_str)

            details["config"] = {
                "provider": provider,
                "model": model_name,
                "dimensions": expected_dim
            }

            # Warn on common mismatches
            if "gemini" in model_name.lower() and expected_dim != 768:
                 details["errors"].append(f"Config Warning: Model '{model_name}' usually uses 768 dims, but configured for {expected_dim}.")
            if "large" in model_name.lower() and expected_dim != 3072:
                 details["errors"].append(f"Config Warning: Model '{model_name}' usually uses 3072 dims, but configured for {expected_dim}.")

            details["steps"].append("Configuration checked")

            # 2. Seeding (Simulating Alice)
            # Use 'System Probe' as company to easily identify and clean if needed (though we keep it for history)
            librarian = LibrarianService()
            source_id = await librarian.archive_sales_pitch(
                company="System Probe",
                job_title="Integrity Check",
                content="This is a generated probe content to verify vector database integrity.",
                references=["probe-ref"]
            )
            details["steps"].append(f"Seeded document: {source_id}")

            # 3. DB Integrity (Wait for Embedding)
            max_retries = 5
            raw_embedding = None
            for _ in range(max_retries):
                db_item = self.supabase_client.table("archon_crawled_pages").select("embedding").eq("source_id", source_id).limit(1).execute()
                if db_item.data and db_item.data[0].get("embedding"):
                    raw_embedding = db_item.data[0].get("embedding")
                    break
                await asyncio.sleep(2)

            if not raw_embedding:
                raise Exception("Embedding generation timed out. Check background workers/triggers.")

            # Parse embedding
            if isinstance(raw_embedding, str):
                vec = json.loads(raw_embedding)
            else:
                vec = raw_embedding

            dim = len(vec)
            details["detected_dimensions"] = dim

            if dim != expected_dim:
                raise Exception(f"Dimension Mismatch! Config expects {expected_dim}, DB has {dim}.")

            details["steps"].append("Embedding Verification Passed")

            # 4. Retrieval Test
            rag = RAGService()
            results = await rag.search_documents(
                query="Integrity Check",
                match_count=5,
                filter_metadata={"knowledge_type": "sales_pitch"}
            )

            if not results:
                raise Exception("Retrieval failed. Document indexed but not found by semantic search.")

            details["steps"].append(f"Retrieval Passed (Found {len(results)} items)")

            return {
                "status": "healthy" if not details["errors"] else "degraded",
                "details": details
            }

        except Exception as e:
            logger.error(f"RAG Integrity Check Failed: {e}")
            details["errors"].append(str(e))
            return {
                "status": "unhealthy",
                "details": details
            }
