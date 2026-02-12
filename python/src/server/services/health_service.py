import datetime

from ..config.logfire_config import get_logger
from ..utils import get_supabase_client
from .search.rag_service import RAGService

logger = get_logger(__name__)

class HealthService:
    """Service for checking the health of the application and its dependencies."""

    def __init__(self):
        self.supabase_client = get_supabase_client()

    def check_database_connection(self) -> bool:
        """Checks if the database connection is active."""
        try:
            # Use 'profiles' instead of 'users' as it's guaranteed to be in public schema
            self.supabase_client.table("profiles").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False

    def check_table_existence(self, table_name: str) -> bool:
        """Checks if a specific table exists in the database."""
        try:
            self.supabase_client.table(table_name).select("id").limit(1).execute()
            return True
        except Exception:
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

        # Use correct prefixed table names for Archon
        tables_to_check = ["archon_projects", "archon_tasks", "profiles", "archon_settings"]
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
        Calculates a weighted System Integrity Score.
        Weightage: Knowledge Alignment (70%) + DB (15%) + Search (15%)
        """
        logger.info("📊 Calculating Composite System Integrity Score...")

        try:
            # 1. DB Connectivity Check (15% weight)
            db_ok = self.check_database_connection()
            db_score = 15.0 if db_ok else 0.0

            if not db_ok:
                return {
                    "status": "unhealthy",
                    "score": 0.0,
                    "details": {"error": "Critical: Database connection lost. System integrity compromised."}
                }

            # 2. Knowledge Alignment Check (70% weight)
            total_res = self.supabase_client.table("archon_sources").select("source_id", count="exact").execute()
            total_count = total_res.count or 0

            alignment_score = 0.0
            indexed_count = 0
            if total_count > 0:
                indexed_res = self.supabase_client.table("archon_crawled_pages")\
                    .select("source_id")\
                    .not_.is_("embedding", "null")\
                    .execute()
                indexed_count = len({row["source_id"] for row in (indexed_res.data or [])})
                alignment_score = (indexed_count / total_count) * 70.0
            else:
                alignment_score = 70.0 # Default full if empty

            # 3. Search Responsiveness Check (15% weight)
            rag = RAGService()
            search_ok = False
            try:
                test_search = await rag.search_documents(query="AI", match_count=1)
                search_ok = len(test_search) > 0
            except Exception:
                search_ok = False

            search_score = 15.0 if search_ok else 0.0

            # 4. Composite Score
            final_score = round(db_score + alignment_score + search_score, 2)

            return {
                "status": "healthy" if final_score >= 95 else ("degraded" if final_score >= 80 else "unhealthy"),
                "score": final_score,
                "details": {
                    "alignment_raw": round((alignment_score / 70.0) * 100, 1) if total_count > 0 else 100.0,
                    "db_connected": db_ok,
                    "search_active": search_ok,
                    "total_sources": total_count,
                    "indexed_sources": indexed_count,
                    "timestamp": datetime.datetime.now(datetime.UTC).isoformat()
                }
            }

        except Exception as e:
            logger.error(f"💥 System Integrity Calculation Failed: {e}")
            return {
                "status": "unhealthy",
                "score": 0.0,
                "details": {"error": str(e)}
            }
